"""Where channel B's two strobe escapes sit: the escape control points of a
reference layout of channel B's two byte lanes on this board, with the
memory at (6.4509, -17.3772) mm turned 180 degrees.

Each pair's ``PairInsertion`` and ``PairPoint`` at each part, on L3_SIG1,
as a position in mm and a heading in degrees from +x, in the frame of the
circuit that holds the part, so they move when that circuit moves. The
FPGA's circuit sits at the board origin, unrotated, so its frame is the
board's; the FPGA sits at (0, 12) in it. The memory's circuit sits at
(6.4509, -17.3772) unrotated, with the memory at its origin turned 180
degrees.

The FPGA's entries are keyed by byte slot of
:py:data:`jitxexamples.jumpstart_kits.vp1002_lpddr4.pinout.LPDDR4_X32`, the
memory's by channel B byte lane (``ch[1].d[k]``). In the reference layout
byte lane 0 (DQS[2]) leaves the FPGA from slot 3's strobe balls and byte
lane 1 (DQS[3]) from slot 2's.

The table holds positions and headings only. Each control point's
``invert`` flag comes from the kit's polarity rule: inverted at the FPGA,
not at the memory.
"""

from types import MappingProxyType
from typing import NamedTuple


class ControlPoint(NamedTuple):
    """A control point's position, mm, and heading, degrees from +x, in its
    part's circuit frame."""

    x: float
    y: float
    heading: float


class PairEscape(NamedTuple):
    """One pair's escape at one part: its insertion beside the pair's two
    vias and its pair point just outside the ball field."""

    insertion: ControlPoint
    point: ControlPoint


FPGA_ESCAPES = MappingProxyType(
    {
        2: PairEscape(
            insertion=ControlPoint(2.6282, -0.42, 180.0),
            point=ControlPoint(1.3821, -5.3816, 270.0),
        ),
        3: PairEscape(
            insertion=ControlPoint(6.9014, 2.3414, 225.0),
            point=ControlPoint(7.9313, -5.3802, 270.0),
        ),
    }
)
"""The FPGA's escapes of channel B's strobes, by byte slot."""

MEMORY_ESCAPES = MappingProxyType(
    {
        0: PairEscape(
            insertion=ControlPoint(2.9593, 4.5487, 0.0),
            point=ControlPoint(3.149, 7.5103, 90.0),
        ),
        1: PairEscape(
            insertion=ControlPoint(-2.7365, 4.5583, 0.0),
            point=ControlPoint(-2.4139, 7.7831, 90.0),
        ),
    }
)
"""The memory's escapes of channel B's strobes, by byte lane of ``ch[1]``."""
