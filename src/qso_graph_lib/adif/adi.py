"""ADI reading and writing. See the package docstring for the rules, and ADIF 3.1.7 IV.A."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field

# A Data-Specifier's tag. The field name may not contain a comma, colon, angle
# bracket or brace (ADIF 3.1.7, Field names); the length is at most nine digits,
# so a forged "<CALL:99999...9>" cannot make a huge integer; the type indicator is
# one letter.
_NAME = r"(?P<name>[^\s:<>,{}]+)"
_TAIL = r":(?P<len>\d{1,9})(?::(?P<type>[A-Za-z]))?"
_LITERAL = re.compile(r"<" + _NAME + _TAIL + r">")
_LITERAL_EOR = re.compile(r"<eor>", re.IGNORECASE)
_LITERAL_EOH = re.compile(r"<eoh>", re.IGNORECASE)
# QRZ's Logbook API sends its markers HTML-escaped ("&lt;call:6&gt;"). Matching
# the escaped form, rather than unescaping the payload first, keeps a value that
# itself contains "&lt;" intact (qrz-mcp found that out the hard way).
_ESCAPED = re.compile(r"(?:<|&lt;)" + _NAME.replace("<>", "<>&;") + _TAIL + r"(?:>|&gt;)")
_ESCAPED_EOR = re.compile(r"(?:<|&lt;)eor(?:>|&gt;)", re.IGNORECASE)
_ESCAPED_EOH = re.compile(r"(?:<|&lt;)eoh(?:>|&gt;)", re.IGNORECASE)
_OPENER = re.compile(r"<")
_ESCAPED_OPENER = re.compile(r"<|&lt;")
_WHITESPACE = re.compile(r"\s*")

# A field name a writer may emit: ADIF's rule, plus printable ASCII.
_WRITABLE_NAME = re.compile(r"^[!-~](?:[ -~]*[!-~])?$")
_NOT_IN_A_NAME = frozenset(",:<>{}")


@dataclass(frozen=True)
class Problem:
    """Something in the input that broke ADIF's rules, and what was done about it."""

    offset: int
    message: str


@dataclass
class Record:
    """One QSO. ``fields`` are keyed by upper-cased name, values exactly as given."""

    fields: dict[str, str] = field(default_factory=dict)
    types: dict[str, str] = field(default_factory=dict)
    start: int = 0  # where the record's text begins and ends, <EOR> included
    end: int = 0


@dataclass
class Document:
    header_text: str = ""  # the Header as written, up to <EOH>; "" when there is none
    header: dict[str, str] = field(default_factory=dict)
    records: list[Record] = field(default_factory=list)
    problems: list[Problem] = field(default_factory=list)


class _Grammar:
    def __init__(self, escaped: bool) -> None:
        self.spec = _ESCAPED if escaped else _LITERAL
        self.eor = _ESCAPED_EOR if escaped else _LITERAL_EOR
        self.eoh = _ESCAPED_EOH if escaped else _LITERAL_EOH
        self.opener = _ESCAPED_OPENER if escaped else _OPENER


def _resumes(text: str, at: int, end: int, g: _Grammar) -> bool:
    """True when, after any whitespace, the text ends or the next tag begins."""
    at = _WHITESPACE.match(text, at, end).end()  # type: ignore[union-attr]
    return at >= end or g.opener.match(text, at) is not None


def _value(
    text: str, start: int, length: int, end: int, g: _Grammar, name: str,
    problems: list[Problem],
) -> tuple[str, int]:
    """The data of one Data-Specifier, and where reading continues.

    The declared length, in characters, unless the text after it is not where the
    next tag or the end would be. Then two repairs, in order, each reported:
    the length counted UTF-8 bytes (a non-compliant writer, since ADI is ASCII), or
    the length runs past the next tag (which would swallow it, <EOR> included).
    """
    stop = start + length
    if stop > end:
        problems.append(
            Problem(start, f"{name}: length {length} runs past the end of the text"))
        stop = end
    if _resumes(text, stop, end, g):
        return text[start:stop], stop
    value = text[start:stop]

    repairs: list[tuple[int, str]] = []
    if not value.isascii():
        counted, at = 0, start
        while at < end and counted < length:
            counted += len(text[at].encode("utf-8"))
            at += 1
        if counted == length:
            repairs.append(
                (at, "its length counts UTF-8 bytes, not characters; ADI is ASCII"))
    tag = g.opener.search(text, start, stop)
    if tag is not None:
        repairs.append((tag.start(), f"its length {length} runs past the next tag"))
    for at, why in repairs:
        if _resumes(text, at, end, g):
            problems.append(Problem(start, f"{name}: {why}; read as {at - start} characters"))
            return text[start:at], at
    return value, stop


def _specifiers(
    text: str, pos: int, end: int, g: _Grammar, problems: list[Problem],
) -> Iterator[tuple[str, int, int, str, str | None, str]]:
    """Events from ``text[pos:end]``: ("field", start, next, name, type, value),
    ("eor", start, next, ...) and ("eoh", start, next, ...)."""
    while pos < end:
        m = g.opener.search(text, pos, end)
        if m is None:
            return  # the rest is text outside Data-Specifiers: ignored
        at = m.start()
        eor = g.eor.match(text, at, end)
        if eor:
            yield ("eor", at, eor.end(), "", None, "")
            pos = eor.end()
            continue
        eoh = g.eoh.match(text, at, end)
        if eoh:
            yield ("eoh", at, eoh.end(), "", None, "")
            pos = eoh.end()
            continue
        spec = g.spec.match(text, at, end)
        if spec is None:
            pos = m.end()  # a "<" that starts nothing: ignored text
            continue
        name = spec.group("name").upper()
        value, pos = _value(text, spec.end(), int(spec.group("len")), end, g, name, problems)
        kind = spec.group("type")
        yield ("field", at, pos, name, kind.upper() if kind else None, value)


def _header_end(text: str, g: _Grammar, problems: list[Problem]) -> tuple[int, int]:
    """Where the Header ends and the records begin: (end of header, start of body)."""
    eoh = g.eoh.search(text)
    if eoh is None:
        return 0, 0
    first_eor = g.eor.search(text)
    if first_eor is not None and first_eor.start() < eoh.start():
        return 0, 0  # an <EOH> after a record is not a Header's end
    if g.opener.match(text, 0):
        # ADIF 3.1.7 IV.A.3: a file whose first character is "<" has no Header. Many
        # writers emit "<ADIF_VER:5>3.1.7<EOH>" anyway, and reading those fields
        # as the first QSO's would be the worse mistake.
        problems.append(Problem(0, "the file starts with '<', which ADIF says means no "
                                   "Header, but has an <EOH>; read what precedes it as "
                                   "the Header"))
    return eoh.start(), eoh.end()


def _records(
    text: str, body: int, g: _Grammar, problems: list[Problem],
) -> Iterator[Record]:
    current: Record | None = None
    for kind, at, nxt, name, type_, value in _specifiers(text, body, len(text), g, problems):
        if kind == "field":
            if current is None:
                current = Record(start=at)
            if name in current.fields:
                problems.append(Problem(at, f"{name} appears twice in one record; "
                                            "the later value is kept"))
            current.fields[name] = value
            if type_:
                current.types[name] = type_
        elif kind == "eor":
            if current is not None:
                current.end = nxt
                yield current
                current = None
        else:
            problems.append(Problem(at, "an <EOH> among the records is ignored"))
    if current is not None:
        problems.append(Problem(current.start, "the last record has no <EOR>; kept"))
        current.end = len(text)
        yield current


def iter_records(
    text: str, *, escaped_markers: bool = False, problems: list[Problem] | None = None,
) -> Iterator[Record]:
    """The records of an ADI text, one at a time, for logs too big to hold twice.

    ``problems``, when given, collects what ``read`` would report.
    """
    found: list[Problem] = problems if problems is not None else []
    text = text[1:] if text.startswith("﻿") else text
    g = _Grammar(escaped_markers)
    _, body = _header_end(text, g, found)
    yield from _records(text, body, g, found)


def read(text: str, *, escaped_markers: bool = False) -> Document:
    """Read an ADI text: its Header, its records, and anything that broke ADIF's rules.

    ``escaped_markers`` also accepts markers sent HTML-escaped (``&lt;call:6&gt;``),
    as QRZ's Logbook API sends them.
    """
    doc = Document()
    text = text[1:] if text.startswith("﻿") else text
    g = _Grammar(escaped_markers)
    header_end, body = _header_end(text, g, doc.problems)
    if body:
        doc.header_text = text[:header_end]
        for kind, _at, _nxt, name, _type, value in _specifiers(
            text, 0, header_end, g, doc.problems,
        ):
            if kind == "field":
                doc.header[name] = value
    doc.records = list(_records(text, body, g, doc.problems))
    return doc


def read_file(
    path: str | os.PathLike[str], *, encoding: str = "utf-8", escaped_markers: bool = False,
) -> Document:
    """Read an ADI file, with its line ends exactly as written.

    Opening an ADI file in Python's text mode translates CR LF to LF, which shortens
    every multi-line value by a character a line and breaks its declared length: on
    ADIF 3.1.7's own test file that is four fields. So the file is read with no newline
    translation. Bytes that are not valid in ``encoding`` become U+FFFD, one each.
    """
    with open(path, encoding=encoding, errors="replace", newline="") as f:
        return read(f.read(), escaped_markers=escaped_markers)


def _specifier(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name}: an ADI value is text, not {type(value).__name__}")
    if not _WRITABLE_NAME.match(name) or _NOT_IN_A_NAME & set(name):
        raise ValueError(f"{name!r} is not an ADIF field name")
    # Length in characters. ADI is ASCII, where that is the byte count too; for a
    # non-ASCII value it is what QRZ declares, and what read() expects first.
    return f"<{name.upper()}:{len(value)}>{value}"


def write(
    records: Iterable[Mapping[str, str]],
    header: Mapping[str, str] | None = None,
    header_text: str | None = None,
) -> str:
    """ADI text for ``records``, one per line, with a Header when one is given.

    A Header must not begin with "<" (ADIF 3.1.7 IV.A.3: a file that does has no
    Header), so one is always opened with text: ``header_text``, or a default.
    """
    out: list[str] = []
    if header is not None or header_text:
        opening = (header_text or "ADIF export").rstrip()
        if not opening or opening[0] == "<":
            raise ValueError("a Header must begin with a character other than '<'")
        out.append(opening + "\n")
        out.extend(_specifier(k, v) + "\n" for k, v in (header or {}).items())
        out.append("<EOH>\n")
    for rec in records:
        out.append("".join(_specifier(k, v) for k, v in rec.items()) + "<EOR>\n")
    return "".join(out)
