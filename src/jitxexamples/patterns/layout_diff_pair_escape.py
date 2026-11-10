"""Neck two differential pairs down at a fine-pitch device with a tag on the
neck routes, and key the pair-to-pair rule on the runs so it stays off the
device.

Use this pattern when pairs leave a device whose pads are too close for the
run width, and the run needs pair-to-pair spacing that the device pins
cannot give. Two lanes leave a fictional device with pads at 0.3 mm pitch,
0.15 mm wide, in the order lane 0 p, lane 0 n, lane 1 p, lane 1 n. A 0.25 mm
run trace centred on one of those pads comes within 0.1 mm of the next pad,
under the 0.127 mm fab floor of the sample substrate, and the two lanes'
inner pads are 0.15 mm apart, well inside a 0.5 mm pair-to-pair spacing.

Each leg is three code routes: a neck from the device pad to a ``RoutePoint``
where the run starts, the run between the two devices' run points, and a
neck from the far run point into the far pad. Three rules apply to the
copper:

1. ``design_constraint(DiffPairTag(), priority=2).trace_width(RUN_WIDTH)``
   on the four nets.
2. ``design_constraint(PairNeckTag(), priority=4).trace_width(neck_width)``
   on the neck ``Route`` objects. The higher priority wins on the necks; the
   runs keep the run width. The neck width is the device pad width less
   0.02 mm, rounded down to 0.01 mm and checked against the pad and the fab
   floor, as in ``layout_qfn_escape``: 0.13 mm here.
3. ``design_constraint(Lane0RunTag(), Lane1RunTag(), priority=2).clearance(PAIR_TO_PAIR)``
   between the two lanes' run ``Route`` objects only. The necks carry
   neither run tag, so the pair-to-pair rule does not reach the device,
   where the pins sit closer than it allows.

The run points are placed from the same numbers: within a lane, p and n
centres sit ``RUN_WIDTH + INTRA_PAIR_GAP`` (0.45 mm) apart, and the two
lanes' inner conductors sit ``PAIR_TO_PAIR`` (0.5 mm) apart edge to edge.
Because the run points already sit at that spacing, the pair-to-pair rule
sets nothing in this design: the 0.5 mm between the runs comes from where
they are placed. The rule takes effect in the failure design below, which
keeps rule 3 unchanged but assigns ``Lane0RunTag`` and ``Lane1RunTag`` to
the lanes' nets instead of their runs, so the rule covers every route of
the two lanes, necks included.

Measured on jitx 4.6, building :py:class:`layout_diff_pair_escape_design`:
every neck realized 0.13 mm wide and every run 0.25 mm, the two lanes' run
copper came no closer than 0.5 mm, and the design's issues listed routing
as satisfied.

Each run goes straight between two placed ``RoutePoint`` objects, and came
back as that straight line. Each neck leaves a pad that sits closer to its
neighbours than the pair-to-pair rule allows, which is why the rule is keyed
on the runs. :py:class:`layout_diff_pair_escape_failure_design` puts the two
lane tags on the nets instead of the runs, so the 0.5 mm rule also covers
the necks, whose pads are 0.15 mm apart. Built on jitx 4.6, one or more
necks came back with no copper, and the issues read
``Unrealizable Route: Insufficient space`` and
``Unable to find path for requested route``.

The widths here are illustrative and not solved for an impedance.

The test, ``tests/test_layout_diff_pair_escape.py``, checks the rules and
the authored geometry offline. With ``JITX_PATTERN_RUNTIME=1`` and a runtime
started at the project root, it builds both designs, measures each
segment's width and the spacing between the lanes' runs on the first, and
reads the issues of both.
"""

from __future__ import annotations

import jitx
from jitx import RoutePoint
from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.constraints import Tag, design_constraint
from jitx.feature import Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import DiffPair, Net, Port
from jitx.sample import SampleDesign
from jitx.shapes.composites import rectangle
from jitxlib.symbols.box import BoxSymbol

from jitxexamples.patterns.layout_qfn_escape import (
    pad_geometry,
    strictly_inside_width,
)

PAD_PITCH = 0.3
"""Centre-to-centre spacing of the device's pads, in mm."""

PAD_WIDTH = 0.15
"""The device pad's short side, across the escape, in mm."""

PAD_LENGTH = 0.6
"""The device pad's long side, along the escape, in mm."""

RUN_WIDTH = 0.25
"""Trace width in the run, in mm."""

INTRA_PAIR_GAP = 0.2
"""Edge-to-edge gap between p and n in the run, in mm."""

PAIR_TO_PAIR = 0.5
"""Edge-to-edge clearance between the two lanes in the run, in mm."""

DEVICE_X = 10.0
"""The devices sit at -DEVICE_X and +DEVICE_X, in mm."""

FAN_RUN = 1.5
"""From a device's pad centres to where the run starts, in mm."""


class DiffPairTag(Tag):
    """Differential pair nets: routed at ``RUN_WIDTH``."""


class PairNeckTag(Tag):
    """Neck segments between a device pad and the run."""


class Lane0RunTag(Tag):
    """Lane 0's run segments."""


class Lane1RunTag(Tag):
    """Lane 1's run segments."""


class DevicePad(Pad):
    shape = rectangle(PAD_LENGTH, PAD_WIDTH)
    soldermask = Soldermask(rectangle(PAD_LENGTH + 0.05, PAD_WIDTH + 0.05))


class DeviceLandpattern(Landpattern):
    """Four pads in a column at ``PAD_PITCH``, top to bottom."""

    pads = [DevicePad().at(0, (1.5 - i) * PAD_PITCH) for i in range(4)]


class FinePitchDevice(Component):
    """A fictional two-lane device with fine-pitch pads. Not a real part."""

    manufacturer = "Fictional"
    mpn = "EXAMPLE-2LANE"
    reference_designator_prefix = "U"

    lane0 = DiffPair()
    lane1 = DiffPair()
    landpattern = DeviceLandpattern()
    symbol = BoxSymbol()

    def __init__(self) -> None:
        pads = self.landpattern.pads
        self.mappings = [
            PadMapping(
                {
                    self.lane0.p: pads[0],
                    self.lane0.n: pads[1],
                    self.lane1.p: pads[2],
                    self.lane1.n: pads[3],
                }
            )
        ]


def run_offsets() -> dict[tuple[int, str], float]:
    """Each conductor's y in the run, keyed by (lane, "p" or "n"). Lane 0 is
    above the axis, lane 1 below, in the device's pin order."""
    inner = PAIR_TO_PAIR / 2 + RUN_WIDTH / 2
    outer = inner + RUN_WIDTH + INTRA_PAIR_GAP
    return {(0, "p"): outer, (0, "n"): inner, (1, "p"): -inner, (1, "n"): -outer}


class TwoLaneLink(Circuit):
    """Two lanes from one device to its mirror image, necked at both ends."""

    def __init__(self, lane_tags_on_nets: bool = False) -> None:
        """``lane_tags_on_nets`` puts the pair-to-pair tags on the nets, the
        mistake the failure design shows."""
        self.near = FinePitchDevice().at(-DEVICE_X, 0)
        self.far = FinePitchDevice().at(DEVICE_X, 0)
        pad = pad_geometry(self.near.landpattern.pads[0])
        minx, miny, maxx, maxy = pad.bounds
        self.neck_width = strictly_inside_width(
            round(min(maxx - minx, maxy - miny), 6),
            jitx.current.substrate.constraints.min_copper_width,
        )

        offsets = run_offsets()
        run_tags: dict[int, type[Tag]] = {0: Lane0RunTag, 1: Lane1RunTag}
        # One entry per conductor, in the same order in every list.
        self.nets: list[Net] = []
        self.points: list[RoutePoint] = []
        self.near_necks: list[Route] = []
        self.runs: list[Route] = []
        self.far_necks: list[Route] = []
        for lane in (0, 1):
            near_pair = self.near.lane0 if lane == 0 else self.near.lane1
            far_pair = self.far.lane0 if lane == 0 else self.far.lane1
            for side in ("p", "n"):
                near_port: Port = getattr(near_pair, side)
                far_port: Port = getattr(far_pair, side)
                y = offsets[(lane, side)]
                start = RoutePoint(layer=0).at(-DEVICE_X + FAN_RUN, y)
                end = RoutePoint(layer=0).at(DEVICE_X - FAN_RUN, y)
                self.points += [start, end]
                net = Net([near_port, far_port], name=f"L{lane}_{side.upper()}")
                net += start.port
                net += end.port
                DiffPairTag().assign(net)
                self.nets.append(net)
                near_neck = Route(near_port, start.pad, layer=0)
                run = Route(start.pad, end.pad, layer=0)
                far_neck = Route(end.pad, far_port, layer=0)
                PairNeckTag().assign(near_neck)
                PairNeckTag().assign(far_neck)
                run_tags[lane]().assign(net if lane_tags_on_nets else run)
                self.near_necks.append(near_neck)
                self.runs.append(run)
                self.far_necks.append(far_neck)

        self.run_rule = design_constraint(DiffPairTag(), priority=2).trace_width(
            RUN_WIDTH
        )
        self.neck_rule = design_constraint(PairNeckTag(), priority=4).trace_width(
            self.neck_width
        )
        self.pair_to_pair_rule = design_constraint(
            Lane0RunTag(), Lane1RunTag(), priority=2
        ).clearance(PAIR_TO_PAIR)


class layout_diff_pair_escape_design(SampleDesign):
    """The two-lane link on the sample board."""

    circuit = TwoLaneLink()


class layout_diff_pair_escape_failure_design(SampleDesign):
    """The same link with the pair-to-pair tags on the nets. The rule then
    covers the necks too, and a neck cannot be routed."""

    circuit = TwoLaneLink(lane_tags_on_nets=True)
