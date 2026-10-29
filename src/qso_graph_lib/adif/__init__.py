"""ADIF's ADI format, read and written as ADIF 3.1.7 defines it.

``read`` and ``iter_records`` take ADI text and return its header and records;
``read_file`` reads a file without translating its line ends, which text mode would;
``write`` makes ADI text. One implementation for the packages that had one each
(lotw-mcp, eqsl-mcp, qrz-mcp, adif-mcp, qsp-client), because they disagreed:
on 2026-10-29 the same input lost a field in one, merged the header into the
first QSO in another, and ran two records together in five of six.

The rules are ADIF's own (ADIF 3.1.7, section IV.A, "ADI File Format"):

- A Data-Specifier is ``<F:L:T>D``: a case-independent field name ``F``, a data
  length ``L``, an optional case-insensitive data type indicator ``T``, then
  exactly ``L`` characters of data. The data is not trimmed.
- A file has a Header only when its first character is not ``<``. The Header
  ends at a case-insensitive ``<EOH>``; its Data-Specifiers are header fields.
- A Record is one or more Data-Specifiers ending in a case-insensitive ``<EOR>``.
- Characters outside Data-Specifiers and tags are ignored.
- ADI is ASCII: the Intl data types "cannot be used in ADI files", so in a
  compliant file a character and a byte are the same count.

Real files are not always compliant, and a reader that gives up loses a log.
Where the input breaks a rule above, the reader repairs what it can and says so
in ``Document.problems``; it never repairs silently.
"""

from .adi import Document, Problem, Record, iter_records, read, read_file, write

__all__ = ["Document", "Problem", "Record", "iter_records", "read", "read_file", "write"]
