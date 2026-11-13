"""UG863's spacing between the VP1002 to Micron LPDDR4 link's signal groups.

Source: AMD, *Versal Adaptive SoC PCB Design User Guide*, UG863 v1.12
(2026-06-16), "Physical Design Rules for LPDDR4/4x Signals", Table 24,
https://docs.amd.com/r/en-US/ug863-versal-pcb-design.

Spacing
-------

Table 24 gives spacing in multiples of H, the height to the nearest ground
plane, and relaxes it "under adaptive SoC or LPDDR4/4x device". Each rule
here is trace to trace only, so pads and vias keep the structure's own
clearance. The ball-field tag (:py:class:`.ball_field.BallFieldTag`) stands
for "under the device". Only a pair's segment inside a ball field carries
it (:py:class:`.ball_field.BallFieldPairTag`, on the strobe escapes); a
single-ended line carries no tag, so it takes the open values under the
device too, the larger ones:

=====================================================  =====  ============
Table 24 relation                                      Open   Under device
=====================================================  =====  ============
Data/strobe between different bytes                    7 H    2 H
CAC/clock to data/strobe, same channel                 7 H    2 H
Signals in one channel to signals in the other         7 H    2 H
Data to strobe, same byte                              5 H    1 H
CAC to clock, same channel                             5 H    2 H
Data to data, same byte; CAC to CAC, same channel      2 H    1 H
=====================================================  =====  ============

:py:func:`spacing_rules` writes the first five rows as rules between the
spacing groups (each byte lane, and each channel's CAC and clock) and
between a group's pairs and its other nets. The last row and the 1 H cases
are left to the structures, whose clearances are larger: SE-46's 6.2 mil
against 2 H = 5.0 mil, and the ball-field pair's clearance of 3.5 mil
against 1 H = 2.5 mil under the device, which is also under the
fabrication floor of 2.8 mil. Rules that keep one net from another are
protections, so they sit above the ball-field structure
(:py:func:`.ball_field.ball_field_rules`, at 4) at 5 to 7, the larger
clearance higher.
"""

from __future__ import annotations

from collections.abc import Sequence

from jitx.constraints import BinaryDesignConstraint, BoolExpr, IsTrace, Tag
from jitx.net import Net

from .ball_field import BallFieldTag


class LPDDR4GroupTag(Tag):
    """A net of one spacing group. Each group is a subclass."""


class ByteLane0Tag(LPDDR4GroupTag):
    """Byte lane 0: channel A, byte 0."""


class ByteLane1Tag(LPDDR4GroupTag):
    """Byte lane 1: channel A, byte 1."""


class ByteLane2Tag(LPDDR4GroupTag):
    """Byte lane 2: channel B, byte 0."""


class ByteLane3Tag(LPDDR4GroupTag):
    """Byte lane 3: channel B, byte 1."""


class CacClockATag(LPDDR4GroupTag):
    """Channel A's command, address, control and clock."""


class CacClockBTag(LPDDR4GroupTag):
    """Channel B's command, address, control and clock."""


class LPDDR4PairTag(Tag):
    """A strobe (DQS) or clock (CK) net."""


BYTE_LANE_TAGS: tuple[type[LPDDR4GroupTag], ...] = (
    ByteLane0Tag,
    ByteLane1Tag,
    ByteLane2Tag,
    ByteLane3Tag,
)
"Spacing group tags of the four byte lanes, in byte-lane order."

CAC_CLOCK_TAGS: tuple[type[LPDDR4GroupTag], ...] = (CacClockATag, CacClockBTag)
"Spacing group tags of the two channels' CAC and clock, A then B."


def spacing_rules(
    byte_lanes: Sequence[Sequence[Net]],
    cac_clock: Sequence[Sequence[Net]],
    pairs: Sequence[Net],
    height: float,
) -> list[BinaryDesignConstraint]:
    """Tag the spacing groups and return UG863's spacing rules between them.

    Args:
        byte_lanes: Each byte lane's nets (DQ, DMI, DQS), in byte-lane order.
        cac_clock: Each channel's CA, CS, CKE and CK nets, A then B.
        pairs: Every DQS and CK net.
        height: H in mm, the height to the nearest ground plane on the
            layers these signals route on.
    """
    if len(byte_lanes) != len(BYTE_LANE_TAGS) or len(cac_clock) != len(CAC_CLOCK_TAGS):
        raise ValueError(
            f"expected {len(BYTE_LANE_TAGS)} byte lanes and "
            f"{len(CAC_CLOCK_TAGS)} channels, got {len(byte_lanes)} and "
            f"{len(cac_clock)}"
        )
    for tag, nets in zip(
        (*BYTE_LANE_TAGS, *CAC_CLOCK_TAGS), (*byte_lanes, *cac_clock), strict=True
    ):
        tag().assign(*nets)
    LPDDR4PairTag().assign(*pairs)

    field: BoolExpr = BallFieldTag() & IsTrace
    open_field: BoolExpr = ~BallFieldTag() & IsTrace
    pair = LPDDR4PairTag()
    rules: list[BinaryDesignConstraint] = []
    for tag in (*BYTE_LANE_TAGS, *CAC_CLOCK_TAGS):
        group = tag()
        others = LPDDR4GroupTag() & ~group
        rules += [
            # Between groups: 7 H in the open, 2 H under the device.
            BinaryDesignConstraint(
                group & open_field, others & open_field, priority=7
            ).clearance(7 * height),
            BinaryDesignConstraint(
                group & field, others & IsTrace, priority=5
            ).clearance(2 * height),
            # A group's strobe or clock to its other nets: 5 H in the open.
            BinaryDesignConstraint(
                group & pair & open_field, group & ~pair & open_field, priority=6
            ).clearance(5 * height),
        ]
    for tag in CAC_CLOCK_TAGS:
        group = tag()
        # Clock to CAC under the device: 2 H, with either side in the field.
        rules += [
            BinaryDesignConstraint(
                group & pair & field, group & ~pair & IsTrace, priority=5
            ).clearance(2 * height),
            BinaryDesignConstraint(
                group & pair & IsTrace, group & ~pair & field, priority=5
            ).clearance(2 * height),
        ]
    return rules
