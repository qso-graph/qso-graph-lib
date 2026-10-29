# Changelog

All notable changes to `qso-graph-lib` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`qso_graph_lib.jt`**: WSJT-X's UDP protocol for the JT family (`protocol`), encoded and decoded
  to `NetworkMessage.hpp`, schema 3, and WSJT-X's `ALL.TXT` reader (`alltxt`). Moved from
  qso-graph-sim, so it and jt-mcp share one implementation.
