"""qso-graph-lib: the code QSO Graph's Python packages share."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Final

try:
    _pkg_version = version("qso-graph-lib")
except PackageNotFoundError:  # source tree without dist metadata
    _pkg_version = "0.0.0-dev"

# Read from the installed distribution, so pyproject.toml is the only place
# the version is written.
__version__: Final[str] = _pkg_version
