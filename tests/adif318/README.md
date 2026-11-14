# ADIF 3.1.8's own test QSO files

From the ADIF project, unchanged: the `318/tests/` files in `ADIF_318_resources_2026_10_12.zip`,
linked from `https://adif.org.uk/318/index.htm`, described in *ADIF 3.1.8 Resources*, section V,
"Test QSO Files based on ADIF Specification Tables". They are built by ADIF's CreateADIFTestFiles
to hold every field and value the specification documents.

| File | SHA-256 |
|---|---|
| `ADIF_318_resources_2026_10_12.zip` (the archive) | `d211e1d41adaf7fc341c73a8a3a56c343534aac57043b7474f7df2d528e56d8c` |
| `ADIF_318_test_QSOs_2026_10_12.adi` | `113369e5c226f090e2caf7db38b3bc6c642054ec4ae8f5b30101a3579a7623b1` |
| `ADIF_318_test_QSOs_2026_10_12.adx` | `81f0ab15f246e483b930543f1a3efd65aa3b1a880e772e76a2f7402fb38e3eeb` |

6,202 QSOs: 3.1.7's 6,197 and five more, for the `JTTY` submode and four SKCC contest IDs that
3.1.8 adds. As with 3.1.7 (`tests/adif317/README.md`), the ADX is the expected answer for reading
the ADI, and `tests/test_adif_spec_files.py` requires them to agree.

The ADIF project's own note applies: do not upload these QSOs to Club Log, LoTW or any other
service. Nothing here does; they are read by tests only.
