# qso-graph-lib

[![PyPI](https://img.shields.io/pypi/v/qso-graph-lib)](https://pypi.org/project/qso-graph-lib/)
[![Python](https://img.shields.io/pypi/pyversions/qso-graph-lib)](https://pypi.org/project/qso-graph-lib/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

The code QSO Graph's Python packages share, in one place, so it is written and tested once. Standard library only: no dependencies.

## What's in it

| Module | What |
|---|---|
| `qso_graph_lib.adif` | ADIF's ADI format, read and written as [ADIF 3.1.7](https://adif.org.uk/317/ADIF_317.htm) defines it. Passes ADIF's own 3.1.7 test files; non-compliant input real logs contain is repaired where it can be and reported in `Document.problems`, never silently |
| `qso_graph_lib.jt.protocol` | WSJT-X's UDP messages, encoded and decoded: Heartbeat, Status, Decode, WSPRDecode, Clear, Close, Replay and the rest, schema 3, written to WSJT-X's own [`Network/NetworkMessage.hpp`](https://github.com/WSJTX/wsjtx/blob/master/Network/NetworkMessage.hpp). That is the JT family's protocol: any program that speaks it (JTDX, MSHV, WSJT-X Improved) is read the same way |
| `qso_graph_lib.jt.alltxt` | WSJT-X's `ALL.TXT`, the log of every decode, read into cycles |

The JT modules are used by [qso-graph-sim](https://github.com/qso-graph/qso-graph-sim) and [jt-mcp](https://github.com/qso-graph/jt-mcp); the ADIF module by the logbook servers and qsp-client.

## Install

```bash
uv add qso-graph-lib
```

Or `pip install qso-graph-lib`. It has no command of its own; it is imported.

## Example

```python
from qso_graph_lib.jt import protocol

message = protocol.parse(datagram)          # ValueError if it isn't a WSJT-X message
if message.kind == protocol.MessageType.DECODE:
    print(message.sender, message.fields["snr"], message.fields["message"])
```

Unknown message types, and fields past the ones it knows, are ignored, as WSJT-X's protocol requires. A message cut short inside a field it needs is refused.

```python
from qso_graph_lib import adif

doc = adif.read_file("log.adi")             # line ends as written, never text mode
for record in doc.records:
    print(record.fields["CALL"], record.fields.get("BAND"))
for problem in doc.problems:                # what broke ADIF's rules, and what was done
    print(problem.offset, problem.message)

text = adif.write(records, header={"ADIF_VER": "3.1.7", "PROGRAMID": "my-app"})
```

## Development

```bash
git clone https://github.com/qso-graph/qso-graph-lib.git
cd qso-graph-lib
uv sync --group dev
uv run pytest
```

## Part of QSO-Graph

This package is part of [qso-graph](https://github.com/qso-graph), tools for amateur radio. See [qso-graph.io](https://qso-graph.io) for documentation.

## License

[GPLv3](LICENSE)
