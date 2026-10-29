"""ADIF 3.1.7's own test files: reading the ADI must give exactly the ADX's QSOs.

The floor for the reader (KI7MT, 2026-10-29): always pass the ADIF project's version tests.
See tests/adif317/README.md for where the files come from.
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from qso_graph_lib.adif import read, read_file, write

HERE = Path(__file__).parent / "adif317"
ADI = HERE / "ADIF_317_test_QSOs_2026_03_22.adi"
ADX = HERE / "ADIF_317_test_QSOs_2026_03_22.adx"
SHA256 = {
    ADI: "7d5e5201a1b34113e098aeb0ba61d7e63eeba17a7f3edc2d37d29b52828d1502",
    ADX: "c9a09c0603144479165469a0054f9af338fc81731ba42f20070b998700a3d271",
}


def _crlf(s: str) -> str:
    # XML normalises line ends to LF (XML 1.0, 2.11); a MultilineString in ADI keeps CR LF.
    return s.replace("\r\n", "\n")


def _adx_name(el: ET.Element) -> str:
    if el.tag == "APP":
        return f"APP_{el.get('PROGRAMID')}_{el.get('FIELDNAME')}".upper()
    if el.tag == "USERDEF":
        return str(el.get("FIELDNAME")).upper()
    return el.tag.upper()


@pytest.fixture(scope="module")
def files() -> tuple[str, ET.Element]:
    for path, digest in SHA256.items():
        # The files are ADIF's, unchanged; and the XML is parsed only once it is known to be.
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path.name
    with open(ADI, encoding="utf-8", newline="") as f:  # line ends as written
        adi = f.read()
    return adi, ET.parse(ADX).getroot()


def test_every_qso_reads_exactly_as_the_adx_has_it(files):
    adi, adx = files
    doc = read(adi)
    expected = [
        {_adx_name(e): _crlf(e.text or "") for e in rec} for rec in adx.iter("RECORD")
    ]
    assert doc.problems == []
    assert len(doc.records) == len(expected) == 6197

    for i, (rec, want) in enumerate(zip(doc.records, expected)):
        got = {k: _crlf(v) for k, v in rec.fields.items()}
        # The only difference the ADIF project documents: the ADX also has the _INTL
        # fields, which ADI cannot carry, and the ADI has their ASCII fields instead.
        intl = {k for k in want if k.endswith("_INTL")}
        assert {k for k in got if k + "_INTL" in intl} | (set(want) - intl) == set(got), i
        same = set(want) - intl
        assert {k: got[k] for k in same} == {k: want[k] for k in same}, i


def test_the_header_reads_as_the_adx_has_it(files):
    adi, adx = files
    doc = read(adi)
    header = adx.find("HEADER")
    assert header is not None
    for el in header:
        if el.tag == "USERDEF":
            # ADI writes a user-defined field's declaration as USERDEFn, "NAME" or
            # "NAME,{enum}" / "NAME,{range}"; ADX as attributes.
            limits = el.get("ENUM") or el.get("RANGE")
            want = f"{el.text},{limits}" if limits else el.text
            assert doc.header[f"USERDEF{el.get('FIELDID')}"] == want
        elif el.tag != "CREATED_TIMESTAMP":  # the two files were made a second apart
            assert doc.header[el.tag] == el.text, el.tag


def test_writing_the_test_file_reads_back_the_same(files):
    adi, _ = files
    doc = read(adi)
    again = read(write((r.fields for r in doc.records), header=doc.header))
    assert again.problems == []
    assert [r.fields for r in again.records] == [r.fields for r in doc.records]
    assert again.header == doc.header


def test_read_file_keeps_line_ends_and_text_mode_would_not(files):
    """Text mode turns CR LF into LF and breaks multi-line fields' lengths; read_file
    does not. Both halves asserted, so the trap stays proven."""
    adi, _ = files
    assert read_file(ADI).problems == []
    assert [r.fields for r in read_file(ADI).records] == [r.fields for r in read(adi).records]
    translated = ADI.read_text(encoding="utf-8")  # what open(path) in text mode gives
    assert read(translated).problems, "text mode should have broken a multi-line length"
