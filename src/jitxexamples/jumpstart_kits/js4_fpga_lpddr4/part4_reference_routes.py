"""Where a reference layout of channel B's two byte lanes runs each signal:
which FPGA ball each memory ball's route starts from, and the path of each
data line and strobe pair.

The reference layout routes every DQ, DMI and DQS of channel B's byte lanes
0 and 1 (``ch[1].d[0]`` and ``ch[1].d[1]``) on L3_SIG1 from the fanout via
in an FPGA ball to the fanout via in a memory ball, with the memory at
(6.4509, -17.3772) mm turned 180 degrees. Its routes fix the pin
assignment: a route between two balls is one choice among the swaps the
FPGA's offer allows (a byte swap within channel B and a bit swap within a
byte, :py:mod:`jitxexamples.jumpstart_kits.vp1002_lpddr4.circuit`), and the
runtime resolves the assignment to the one the routes match.

Byte lanes are keyed by their index in ``ch[1].d``, FPGA byte slots by
their index in
:py:data:`jitxexamples.jumpstart_kits.vp1002_lpddr4.pinout.LPDDR4_X32`, and
a slot's DQ balls by their index in its ``dq`` positions.

Positions are board-absolute, mm, with headings in degrees from +x: the
frame of the circuit that declares the routes, which sits at the board
origin unrotated. A path's turns lie within 0.15 mm of the reference
layout's centreline, in order from the FPGA end: its corners, simplified to
within 0.03 mm; on each data line the points where it crosses one ball
pitch outside each ball field (y -5.48 below the FPGA's, y -9.902 above the
memory's) and 0.15 mm above the memory's first ball row (y -10.402); and,
on some lines, a point beside a neighbouring line or a strobe pair. A turn
tells the router which side of an obstacle to pass; the router pulls the
route tight between them.

A data line runs from via to via with a control point only where one is
needed: a route point at each end of its length-matching section, on the
four lines where the reference layout matches length (byte lane 0's DQ7
and byte lane 1's DQ0, DQ6 and DQ7). Byte lane 1's DQ6 section takes a
narrower envelope (``envelope``), as DQ5 and DQ7 run close either side of
it. Each section's ends lie within 0.25 mm of the reference layout's: byte
lane 0's DQ7 section starts 0.24 mm further along its path, so the route
point there clears DQ6. A data line carries no tag: inside a ball field it
keeps the 46 ohm structure, which fits between the balls
(:py:mod:`.ball_field`).

A strobe pair's length-matching section runs between two pair points,
placed where the lines either side leave room for the section's ends: a
control point that ends a length-matching section grows to the section's
envelope. Byte lane 1's sit on the reference pair's centreline. Byte lane
0's FPGA-side point does too, and its section bows 0.08 mm off that
centreline, away from DQ6 toward DQ0, for the same reason. Its memory-side
point sits 0.4669 mm straight above Part 1's memory pair point, so the
pair's last leg runs straight down into it and DQ0 passes the pair's end
beside a straight leg rather than a turn.
"""

from types import MappingProxyType
from typing import NamedTuple

from .reference_escapes import ControlPoint

type Turns = tuple[tuple[float, float], ...]
"""Turns of a route, (x, y) in mm, in order from the FPGA end."""


class LinePath(NamedTuple):
    """The path of one data line, from the FPGA via to the memory via. With
    no ``points``, one leg from via to via; with two, three legs, the middle
    one the line's length-matching section between them. Each leg runs
    through its turns."""

    legs: tuple[Turns, ...]
    points: tuple[ControlPoint, ...]
    """The two ends of the line's length-matching section, FPGA side first,
    or none for a line with no section."""
    envelope: float | None = None
    """Envelope overhead, mm, of the length-matching section, where the
    lines beside it leave less room than the default
    (:py:data:`.part4_routing.LINE_ENVELOPE`)."""


class PairPath(NamedTuple):
    """The middle path of one strobe pair, from Part 1's FPGA pair point to
    its memory pair point: three legs joined at two pair points, the middle
    leg the pair's length-matching section."""

    legs: tuple[Turns, Turns, Turns]
    points: tuple[ControlPoint, ControlPoint]


BYTE_SLOTS = MappingProxyType({0: 3, 1: 2})
"""The FPGA byte slot each of channel B's byte lanes leaves from. Byte lane
0 takes slot 3 and byte lane 1 slot 2, a byte swap from slot k = byte k,
where Part 1's strobe escapes (:py:mod:`.reference_escapes`) leave them."""

DQ_BITS = MappingProxyType(
    {
        0: (5, 3, 1, 0, 2, 4, 6, 7),
        1: (3, 0, 2, 6, 4, 5, 7, 1),
    }
)
"""For each byte lane, the FPGA ball each memory DQ bit's route starts
from: entry ``b`` is the index, in the slot's ``dq`` positions, of the ball
that memory ``dq[b]`` connects to."""

DQ_PATHS = MappingProxyType(
    {
        (0, 0): LinePath(
            (
                (
                    (8.4478, 0.3294),
                    (8.6095, 0.1003),
                    (8.6301, -1.8295),
                    (8.7726, -4.5821),
                    (9.0536, -5.48),
                    (10.22, -9.32),
                    (10.1742, -9.902),
                    (10.1349, -10.402),
                ),
            ),
            (),
        ),
        (0, 1): LinePath(
            (
                (
                    (6.1935, 3.0096),
                    (6.3806, 3.118),
                    (6.5941, 3.0845),
                    (7.2924, 2.4845),
                    (8.4292, 1.0805),
                    (8.828, 0.201),
                    (8.866, -1.8173),
                    (9.0085, -4.5699),
                    (9.2946, -5.48),
                    (10.4684, -9.2136),
                    (10.42, -9.902),
                    (10.4102, -10.402),
                    (10.3677, -11.2681),
                ),
            ),
            (),
        ),
        (0, 2): LinePath(
            (
                (
                    (9.3141, 1.1141),
                    (9.3851, 1.012),
                    (9.6926, -4.5832),
                    (9.8889, -5.48),
                    (10.71, -9.11),
                    (10.664, -9.902),
                    (10.635, -10.402),
                    (10.5979, -11.3209),
                    (10.4355, -11.7491),
                ),
            ),
            (),
        ),
        (0, 3): LinePath(
            (
                (
                    (9.346, 2.0051),
                    (9.6136, 1.0699),
                    (9.9285, -4.5704),
                    (10.1275, -5.48),
                    (10.9048, -9.0328),
                    (10.91, -9.902),
                    (10.8649, -10.402),
                    (10.8382, -11.3197),
                    (10.6632, -11.8127),
                    (10.367, -13.2188),
                ),
            ),
            (),
        ),
        (0, 4): LinePath(
            (
                (
                    (5.6341, 1.1141),
                    (5.7042, 1.0153),
                    (5.8535, -0.8541),
                    (6.0241, -4.6609),
                    (6.2228, -5.48),
                    (7.2958, -9.902),
                    (7.4171, -10.402),
                    (7.4645, -10.5975),
                    (7.8314, -11.136),
                    (7.9009, -11.9539),
                    (8.1471, -13.2636),
                ),
            ),
            (),
        ),
        (0, 5): LinePath(
            (
                (
                    (6.117, 0.042),
                    (6.106, -1.8173),
                    (6.2485, -4.5699),
                    (6.5019, -5.48),
                    (7.7331, -9.902),
                    (7.8723, -10.402),
                    (8.0631, -11.0871),
                    (8.1345, -11.9175),
                    (8.2631, -12.541),
                ),
            ),
            (),
        ),
        (0, 6): LinePath(
            (
                (
                    (6.7511, -0.793),
                    (7.0101, -1.7733),
                    (7.2048, -5.48),
                    (7.2192, -5.7545),
                    (7.298, -5.9832),
                    (7.71, -6.8),
                    (8.3876, -8.5994),
                    (8.7222, -9.902),
                    (8.8506, -10.402),
                    (8.8766, -10.5034),
                    (8.7558, -11.3105),
                ),
            ),
            (),
        ),
        (0, 7): LinePath(
            (
                (
                    (6.7741, -1.7843),
                    (6.9507, -5.48),
                    (6.9582, -5.6361),
                ),
                (),
                (
                    (8.4222, -9.902),
                    (8.5974, -10.402),
                    (8.6416, -10.528),
                ),
            ),
            (
                ControlPoint(7.456, -7.155, 109.427),
                ControlPoint(8.0122, -8.7318, 109.427),
            ),
        ),
        (1, 0): LinePath(
            (
                (
                    (0.5083, -1.6813),
                    (0.3493, -3.64),
                    (0.3549, -4.6398),
                    (0.4735, -5.48),
                ),
                (),
                (
                    (2.1225, -9.902),
                    (2.4026, -10.402),
                ),
            ),
            (
                ControlPoint(0.7347, -7.3306, 115.68),
                ControlPoint(1.6041, -8.9765, 115.68),
            ),
        ),
        (1, 1): LinePath(
            (
                (
                    (0.8059, -1.6459),
                    (0.7358, -1.7447),
                    (0.5865, -3.6141),
                    (0.5855, -4.56),
                    (0.76, -5.48),
                    (0.8, -5.9),
                    (2.6293, -9.902),
                    (2.8578, -10.402),
                    (3.1669, -11.1326),
                    (3.1564, -11.3089),
                ),
            ),
            (),
        ),
        (1, 2): LinePath(
            (
                (
                    (-0.1918, -1.8),
                    (-0.1918, -4.56),
                    (-0.0474, -5.48),
                    (0.2551, -7.4063),
                    (1.0391, -9.902),
                    (1.1962, -10.402),
                    (1.8881, -12.6046),
                ),
            ),
            (),
        ),
        (1, 3): LinePath(
            (
                (
                    (-0.1141, 0.1941),
                    (-0.1898, 0.0674),
                    (-0.428, -1.8),
                    (-0.4228, -4.6267),
                    (-0.2858, -5.48),
                    (0.0461, -7.5468),
                    (0.7862, -9.902),
                    (0.9433, -10.402),
                    (1.6522, -12.6578),
                    (1.9227, -13.2955),
                ),
            ),
            (),
        ),
        (1, 4): LinePath(
            (
                (
                    (4.0009, 0.0768),
                    (4.1052, -0.8312),
                    (4.0293, -2.72),
                    (4.0341, -4.6376),
                    (4.3893, -5.48),
                    (5.1085, -7.186),
                    (5.4169, -8.7671),
                    (5.5827, -9.902),
                    (5.6557, -10.402),
                    (5.6792, -10.563),
                    (5.4296, -11.2719),
                    (5.0753, -11.7739),
                    (4.767, -13.2188),
                ),
            ),
            (),
        ),
        (1, 5): LinePath(
            (
                (
                    (3.8723, -0.8806),
                    (3.4906, -1.7703),
                    (3.3496, -2.6681),
                    (3.3517, -4.6266),
                    (3.9184, -5.48),
                    (4.3724, -6.1637),
                    (4.8778, -7.2398),
                    (5.1833, -8.802),
                    (5.33, -9.902),
                    (5.4224, -10.402),
                    (5.4406, -10.5239),
                    (5.4057, -10.6654),
                    (5.0709, -11.1362),
                    (4.8552, -11.6892),
                ),
            ),
            (),
        ),
        (1, 6): LinePath(
            (
                (
                    (2.9246, 0.318),
                    (3.064, 0.1508),
                    (3.1137, -4.6347),
                    (3.1815, -4.8379),
                    (3.5395, -5.48),
                ),
                (),
                (
                    (4.9676, -9.902),
                    (5.0, -10.402),
                    (4.8733, -10.6213),
                    (4.7558, -11.3105),
                ),
            ),
            (
                ControlPoint(4.08, -6.39, 294.5),
                ControlPoint(4.835, -8.86, 283.2),
            ),
            envelope=0.15,
        ),
        (1, 7): LinePath(
            (
                (
                    (2.4326, -4.6286),
                    (2.809, -5.48),
                ),
                (),
                (
                    (4.5, -8.9),
                    (4.7, -9.902),
                    (4.66, -10.402),
                    (4.6423, -10.5406),
                ),
            ),
            (
                ControlPoint(2.9256, -5.7437, 114.215),
                ControlPoint(3.9065, -7.5562, 114.215),
            ),
        ),
    }
)
"""Each DQ line's path, keyed by (byte lane, memory DQ bit)."""

DMI_PATHS = MappingProxyType(
    {
        0: LinePath(
            (
                (
                    (4.7905, 0.0621),
                    (5.3348, -4.6097),
                    (5.5683, -5.48),
                    (6.7547, -9.902),
                    (6.8889, -10.402),
                    (7.4657, -12.5519),
                    (7.8309, -13.0862),
                    (8.173, -13.968),
                    (8.3341, -14.104),
                    (8.5448, -14.1118),
                    (8.6813, -14.0294),
                    (8.7618, -13.8918),
                    (8.9435, -12.4013),
                ),
            ),
            (),
        ),
        1: LinePath(
            (
                (
                    (3.7773, 1.268),
                    (3.914, 1.1834),
                    (3.9922, 1.0429),
                    (4.2356, 0.1038),
                    (4.3399, -0.8042),
                    (4.2655, -2.72),
                    (4.272, -4.628),
                    (4.6333, -5.48),
                    (5.3495, -7.1692),
                    (5.6447, -8.6978),
                    (5.8251, -9.902),
                    (5.9, -10.402),
                    (5.9078, -10.4541),
                    (5.4406, -13.8301),
                    (5.357, -13.9625),
                    (4.4509, -14.1258),
                    (3.6194, -13.9914),
                    (3.5019, -13.9238),
                    (3.3345, -13.2175),
                    (3.3278, -12.5022),
                    (3.3706, -12.3417),
                ),
            ),
            (),
        ),
    }
)
"""Each DMI line's path, keyed by byte lane."""


PAIR_PATHS = MappingProxyType(
    {
        0: PairPath(
            ((), ((8.503, -6.689),), ()),
            (
                ControlPoint(8.18, -6.048, 290.4),
                ControlPoint(9.6, -9.4, 270.0),
            ),
        ),
        1: PairPath(
            (
                ((1.4487, -5.8294), (1.7287, -6.2941)),
                (
                    (2.2036, -6.7285),
                    (2.4395, -7.1147),
                    (2.4986, -7.319),
                    (2.5317, -7.7803),
                    (2.7522, -8.1775),
                ),
                (
                    (3.0168, -8.4307),
                    (3.5049, -8.6055),
                    (3.8855, -8.9559),
                    (4.0366, -9.2743),
                ),
            ),
            (
                ControlPoint(2.124, -6.656, 317.6),
                ControlPoint(2.929, -8.346, 316.3),
            ),
        ),
    }
)
"""Each strobe pair's middle path, keyed by byte lane. Its turns follow the
reference layout's coupled centreline. Byte lane 0's first and last legs
run straight, and its middle leg turns once, for the bow."""
