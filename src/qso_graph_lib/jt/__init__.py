"""The JT family's UDP protocol, as WSJT-X defines it, and WSJT-X's ALL.TXT.

``protocol`` encodes and decodes WSJT-X's UDP messages, schema 3, written to
``Network/NetworkMessage.hpp``. Any program that speaks that protocol (JTDX,
MSHV, WSJT-X Improved) is read the same way; one that does not is not this.
``alltxt`` reads the log WSJT-X keeps of every decode.
"""

from . import alltxt, protocol

__all__ = ["alltxt", "protocol"]
