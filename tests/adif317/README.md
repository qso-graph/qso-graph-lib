# ADIF 3.1.7's own test QSO files

From the ADIF project, unchanged: the `317/tests/` files in
`https://adif.org.uk/317/resources` (`ADIF_317_resources_2026_03_22.zip`), described in
*ADIF 3.1.7 Resources*, section V, "Test QSO Files based on ADIF Specification Tables". They are
built by ADIF's CreateADIFTestFiles to hold every field and value the specification documents.

| File | SHA-256 |
|---|---|
| `ADIF_317_resources_2026_03_22.zip` (the archive) | `1a70caf3a152c67c23ce9c4681f24b8e5f814862d8153d9a72e741375358e6d9` |
| `ADIF_317_test_QSOs_2026_03_22.adi` | `7d5e5201a1b34113e098aeb0ba61d7e63eeba17a7f3edc2d37d29b52828d1502` |
| `ADIF_317_test_QSOs_2026_03_22.adx` | `c9a09c0603144479165469a0054f9af338fc81731ba42f20070b998700a3d271` |

The ADI and ADX files hold the same QSOs, except that the ADX also has the `_INTL` fields, which
ADI cannot carry. So the ADX is the expected answer for reading the ADI:
`tests/test_adif_spec_files.py` reads one with `qso_graph_lib.adif` and the other as XML and
requires them to agree. **Passing these is the floor** (KI7MT, 2026-10-29); `tests/test_adif.py`
adds the non-compliant input real logs contain, which ADIF's files do not.

The ADIF project's own note applies: do not upload these QSOs to Club Log, LoTW or any other
service. Nothing here does; they are read by tests only.

For a new ADIF version, add its directory beside this one rather than replacing it.
