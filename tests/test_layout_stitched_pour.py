"""Tests for the stitched pour pattern.

The offline tests check the rule against the substrate it runs on. The runtime
test, gated by ``JITX_PATTERN_RUNTIME=1``, submits the design and checks the
generated vias against the sites ``expected_stitch_sites`` derives from the
captured pour. The offline tests of that function work their expected sites
out by hand from each test's own pour, pad and via geometry, using the
placement rule measured on jitx 4.6: sites on an absolute grid, kept when a
circle of radius ``pad / 2 + inset`` fits inside the computed pour copper.
"""

import os
import shutil
import unittest
from pathlib import Path

import jitx
from jitx.constraints import (
    AtomExpr,
    SquareViaStitchGrid,
    Tags,
    TriangularViaStitchGrid,
)
from jitx.copper import Pour
from jitx.inspect import extract, visit
from jitx.run.runtime import RuntimeDesign
from jitx.substrate import FabricationConstraints
from jitx.test import TestCase
from jitx.via import Via
from shapely.geometry import Point, Polygon, box
from shapely.geometry.base import BaseGeometry

from jitxexamples.patterns.layout_stitched_pour import (
    INSET_SLACK,
    StitchedPour,
    StitchedPourTag,
    checked_stitch_grid,
    expected_stitch_sites,
    layout_stitched_pour_design,
)


class _PadBoundFab(FabricationConstraints):
    """Fab floors where copper-to-copper spacing would push the pitch past the
    pad, if it applied between same-net vias."""

    min_copper_width = 0.1
    min_copper_copper_space = 0.1
    min_copper_hole_space = 0.2
    min_copper_edge_space = 0.3
    min_annular_ring = 0.125
    min_drill_diameter = 0.2
    min_hole_to_hole = 0.25


class _LooseDrillFab(_PadBoundFab):
    """Drill plus min_hole_to_hole is 0.25 + 0.15 = 0.4, under the 0.5 pad."""

    min_hole_to_hole = 0.15


class _HalfMillimetreVia(Via):
    start_layer = 0
    stop_layer = 1
    diameter = 0.5
    hole_diameter = 0.25


class TestStitchFloor(unittest.TestCase):
    """The floor for a 0.5 mm pad, 0.25 mm drill via.

    On ``_PadBoundFab`` drill plus min_hole_to_hole is 0.25 + 0.25 = 0.5, and
    one pad is 0.5. The 0.1 mm min_copper_copper_space does not add to the
    pad: clearance is not enforced between copper of the same net, and stitch
    vias take the pour's net. So 0.5 is buildable.

    On ``_LooseDrillFab`` the drill floor is 0.4, so only the pad refuses
    0.49: below one pad the runtime thins the grid to a checkerboard
    (measured on jitx 4.6).
    """

    def test_accepts_one_pad_without_copper_spacing(self) -> None:
        grid = checked_stitch_grid(_HalfMillimetreVia, _PadBoundFab(), 0.5, 0.4)
        self.assertEqual(grid.pitch, 0.5)

    def test_refuses_below_one_pad(self) -> None:
        with self.assertRaisesRegex(ValueError, "is below"):
            checked_stitch_grid(_HalfMillimetreVia, _LooseDrillFab(), 0.49, 0.4)


def _lattice(xs: tuple[float, ...], ys: tuple[float, ...]) -> set[tuple[float, float]]:
    return {(x, y) for x in xs for y in ys}


class TestExpectedStitchSites(unittest.TestCase):
    """Sites for the 0.5 mm pad via on a 2.0 mm grid with a 0.5 mm inset.

    A site is kept when a circle of radius 0.25 + 0.5 = 0.75, plus the inset
    slack, around it fits in the pour. On ``_PadBoundFab`` the pad margin is 0.1 mm, so a site is
    left out when its centre is under 0.25 + 0.1 = 0.35 from a pad, or under
    0.5 + 0.1 = 0.6 from a code-placed via.
    """

    grid = SquareViaStitchGrid(pitch=2.0, inset=0.5)
    square = box(0, 0, 10, 10)
    """Sites at 2, 4, 6 and 8 in each axis: 0.75 to 9.25 holds them all."""

    def _sites(
        self,
        pours: list[BaseGeometry],
        pads: tuple[BaseGeometry, ...] = (),
        placed_vias: tuple[tuple[float, float], ...] = (),
        leave_out: BaseGeometry | None = None,
    ) -> set[tuple[float, float]]:
        return expected_stitch_sites(
            pours,
            _HalfMillimetreVia,
            self.grid,
            _PadBoundFab(),
            pads=pads,
            placed_vias=placed_vias,
            leave_out=leave_out,
        )

    def test_lattice_is_on_the_board_origin_and_the_pad_grows_by_the_inset(
        self,
    ) -> None:
        # The pour spans 1 to 8.6. Grown pads fit with centres from 1.75 to
        # 7.85: sites 2, 4 and 6. A lattice from the pour's corner would put
        # sites at 3, 5 and 7; a pad not grown by the inset would fit site 8
        # (8 + 0.25 < 8.6).
        sites = self._sites([box(1, 1, 8.6, 8.6)])
        self.assertEqual(sites, _lattice((2, 4, 6), (2, 4, 6)))

    def test_a_site_must_fit_every_stitched_pour(self) -> None:
        # The second pour ends at x 6.5, so only x 2 and 4 fit both
        # (4 + 0.75 <= 6.5 < 6 + 0.75).
        sites = self._sites([self.square, box(0, 0, 6.5, 10)])
        self.assertEqual(sites, _lattice((2, 4), (2, 4, 6, 8)))

    def test_sites_near_a_pad_are_left_out(self) -> None:
        # Pad edges 0.34 from site (4, 4), under 0.35, and 0.36 from (6, 4).
        pads = (box(4.34, 3.5, 5.0, 4.5), box(6.36, 3.5, 7.0, 4.5))
        sites = self._sites([self.square], pads=pads)
        self.assertEqual(sites, _lattice((2, 4, 6, 8), (2, 4, 6, 8)) - {(4, 4)})

    def test_sites_near_a_code_placed_via_are_left_out(self) -> None:
        # Centres 0.55 from (4, 4), under 0.6, and 0.62 from (8, 6).
        placed = ((4.55, 4.0), (8.0, 6.62))
        sites = self._sites([self.square], placed_vias=placed)
        self.assertEqual(sites, _lattice((2, 4, 6, 8), (2, 4, 6, 8)) - {(4, 4)})

    def test_a_left_out_region_drops_its_sites(self) -> None:
        sites = self._sites([self.square], leave_out=box(0, 0, 10, 3))
        self.assertEqual(sites, _lattice((2, 4, 6, 8), (4, 6, 8)))

    def test_slack_covers_every_measured_inset_window(self) -> None:
        # Measured on jitx 4.6 (predicted threshold, smallest distance kept):
        # 0.725 and 0.73; 0.862 and 0.88; 0.562 and 0.58. A site between the
        # threshold and the keep was not measured, so it must not be required.
        for predicted, kept in ((0.725, 0.73), (0.862, 0.88), (0.562, 0.58)):
            self.assertGreaterEqual(INSET_SLACK, kept - predicted - 1e-9)

    def test_a_site_within_the_slack_is_not_required(self) -> None:
        # Site x 8 needs the pour's right edge at 8 + 0.75 + slack. Half the
        # slack short leaves it out; past the slack keeps it.
        short = box(0, 0, 8.75 + INSET_SLACK / 2, 10)
        self.assertNotIn((8, 4), self._sites([short]))
        clear = box(0, 0, 8.75 + INSET_SLACK + 0.005, 10)
        self.assertIn((8, 4), self._sites([clear]))

    def test_refuses_a_grid_it_does_not_derive(self) -> None:
        with self.assertRaisesRegex(ValueError, "TriangularViaStitchGrid"):
            expected_stitch_sites(
                [self.square],
                _HalfMillimetreVia,
                TriangularViaStitchGrid(pitch=2.0, inset=0.5),
                _PadBoundFab(),
            )

    def test_refuses_no_pours_or_an_empty_one(self) -> None:
        with self.assertRaisesRegex(ValueError, "no pours given"):
            self._sites([])
        cases: list[tuple[list[BaseGeometry], str]] = [
            ([Polygon(), self.square], "pour 0 is empty"),
            ([self.square, Point(0, 0).buffer(0)], "pour 1 is empty"),
        ]
        for pours, which in cases:
            with self.subTest(which), self.assertRaisesRegex(ValueError, which):
                self._sites(pours)

    def test_refuses_a_pitch_below_one_pad(self) -> None:
        with self.assertRaisesRegex(ValueError, "is below"):
            expected_stitch_sites(
                [self.square],
                _HalfMillimetreVia,
                SquareViaStitchGrid(pitch=0.45, inset=0.5),
                _LooseDrillFab(),
            )


def _generated_via_centres(rd: RuntimeDesign) -> set[tuple[float, float]]:
    """Centres, to 1 um, of the vias the runtime generated.

    ``rd.query(Via)`` returns the generated vias together with the vias the
    design places in code. The code-placed ones are the ``Via`` objects in the
    captured tree, which ``visit`` lists and the query yields as themselves,
    so they are left out by identity.
    """
    placed = {id(via) for _, via in visit(rd.root, Via)}
    centres = set()
    for trace, via in rd.query(Via):
        if id(via) in placed:
            continue
        assert trace.transform is not None and via.transform is not None
        x, y = (trace.transform * via.transform).translation
        centres.add((round(x, 3), round(y, 3)))
    return centres


def _tagged(obj: object) -> set[type]:
    tags = Tags.get(obj)
    return {type(t) for t in tags.tags} if tags else set()


class TestStitchedPourRule(TestCase):
    def setUp(self) -> None:
        self.design = layout_stitched_pour_design()
        circuit = self.design.circuit
        assert isinstance(circuit, StitchedPour)
        self.circuit: StitchedPour = circuit
        self.rule = self.circuit.stitch_rule
        stitch = self.rule.stitch_via_constraint
        assert stitch is not None
        self.stitch = stitch
        assert isinstance(stitch.definition, type)
        self.via: type[Via] = stitch.definition
        self.fab = self.design.substrate.constraints

    def test_rule_targets_the_top_pour_only(self) -> None:
        condition = self.rule.condition
        assert isinstance(condition, AtomExpr)
        self.assertIsInstance(condition.atom, StitchedPourTag)
        tagged = [
            p for p in extract(self.circuit, Pour) if StitchedPourTag in _tagged(p)
        ]
        self.assertEqual([p.layer for p in tagged], [0])
        self.assertNotIn(StitchedPourTag, _tagged(self.circuit.GND))

    def test_pitch_keeps_the_fab_spacings(self) -> None:
        # A pitch below one via pad is thinned to a checkerboard, and the
        # fab sheet puts drills at least min_hole_to_hole apart edge to edge.
        # The runtime checks neither (measured on jitx 4.6), so the pattern
        # has to. Same-net pads need no copper spacing: clearance is not
        # enforced between copper of the same net.
        pitch = self.stitch.pattern.pitch
        self.assertGreaterEqual(pitch, float(self.via.diameter))
        self.assertGreaterEqual(
            pitch - self.via.hole_diameter, self.fab.min_hole_to_hole
        )

    def test_checked_grid_refuses_the_pitch_the_runtime_accepted(self) -> None:
        # Measured on jitx 4.6: with this via (0.45 mm pad, 0.3 mm drill) a
        # 0.5 mm pitch put drills 0.2 mm apart, under the sample fab sheet's
        # min_hole_to_hole, and the runtime raised no issue. The pads clear
        # each other, so a floor of one pad diameter would accept it.
        with self.assertRaisesRegex(ValueError, "is below"):
            checked_stitch_grid(self.via, self.fab, 0.5, 0.4)

    def test_pour_has_a_same_net_anchor_inside_it(self) -> None:
        # A pour with no object of its own net comes back empty (measured on
        # jitx 4.6).
        pour = self.circuit.gnd_pour.shape.to_shapely().g
        anchor = self.circuit.gnd_anchor
        assert anchor.transform is not None
        x, y = anchor.transform.translation
        self.assertTrue(pour.contains(Point(x, y)))
        self.assertIn(anchor, self.circuit.GND.connected)


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestStitchedPourRuntime(TestCase):
    def test_vias_fill_the_computed_pour_on_the_absolute_grid(self) -> None:
        design = layout_stitched_pour_design
        root = Path(__file__).resolve().parents[1]
        shutil.rmtree(
            root / "designs" / f"{design.__module__}.{design.__qualname__}",
            ignore_errors=True,
        )
        with jitx.runtime as rt:
            rd = rt.submit(design)
            rd.capture(wait=30)
            circuit = rd.root.circuit
            assert isinstance(circuit, StitchedPour)
            pour = circuit.gnd_pour.shape.to_shapely().g
            stitch = circuit.stitch_rule.stitch_via_constraint
            assert stitch is not None and isinstance(stitch.definition, type)
            assert isinstance(stitch.pattern, SquareViaStitchGrid)
            placed = []
            for trace, via in visit(rd.root, Via):
                assert trace.transform is not None and via.transform is not None
                placed.append((trace.transform * via.transform).translation)
            vias = _generated_via_centres(rd)
            fab = rd.root.substrate.constraints

        expected = expected_stitch_sites(
            [pour], stitch.definition, stitch.pattern, fab, placed_vias=placed
        )
        self.assertGreater(len(expected), 0)
        # Nothing in this design is left out by a margin, so the generated
        # set is exactly the derived one (measured on jitx 4.6).
        self.assertEqual(vias, {(round(x, 3), round(y, 3)) for x, y in expected})
