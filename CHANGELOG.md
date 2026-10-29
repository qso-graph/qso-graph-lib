# Changelog

All notable changes to `qso-graph-lib` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-29

### Added

- **`qso_graph_lib.adif`**: ADIF's ADI format, read and written as ADIF 3.1.7 defines it
  (section IV.A): `read`, `iter_records` (streaming), `read_file` and `write`. One
  implementation for lotw-mcp, eqsl-mcp, qrz-mcp, adif-mcp and qsp-client, whose six parsers
  disagreed: the same input dropped a field in one, merged the Header into the first QSO in
  another, and ran two records together in five of six.
  - **Passes ADIF 3.1.7's own test files**: all 6,197 QSOs of `ADIF_317_test_QSOs` read exactly
    as its ADX twin has them, with no problem reported. The files are in `tests/adif317/`,
    checked by SHA-256, and passing them is the floor.
  - Non-compliant input that real logs contain (a length counted in UTF-8 bytes, a length that
    runs past the next tag, a Header starting with `<`, a last record without `<EOR>`) is
    repaired where it can be and **reported** in `Document.problems`, never silently.
  - `read_file` reads without newline translation. Text mode turns CR LF into LF and breaks
    every multi-line field's declared length: four fields in ADIF's test file.
  - QRZ's HTML-escaped markers (`&lt;call:6&gt;`) are read with `escaped_markers=True`,
    without rewriting the values.
  - `write` checks field names and always opens a Header with text, as a Header that begins
    with `<` is, by the specification, no Header.

## [0.1.0] - 2026-10-29

### Added

- **`qso_graph_lib.jt`**: WSJT-X's UDP protocol for the JT family (`protocol`), encoded and decoded
  to `NetworkMessage.hpp`, schema 3, and WSJT-X's `ALL.TXT` reader (`alltxt`). Moved from
  qso-graph-sim, so it and jt-mcp share one implementation.
