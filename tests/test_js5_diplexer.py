"""JS5: tests for the diplexer board reference solution.

The outline, port positions and holes are the requirements of
``jumpstart-kits/js5-diplexer/JS5_Diplexer-from-Spec_Runbook.md``: the
ZDPLX-592-S+ case, 31.75 mm square; common port at the left edge and high port
at the right, both 16.00 mm from the top edge; low port at the bottom edge,
16.00 mm from the left; two 3.18 mm holes at the top-left and bottom-right
corners, 25.40 mm apart each way. The board is centred on the origin, so an
edge sits at +/-15.875 mm and 16.00 mm from an edge is 0.125 mm past the
centre line. The part numbers are the ones the user approved at the end of the
run that produced this board.
"""

from functools import cache

from jitx.board import Board
from jitx.feature import Cutout
from jitx.inspect import extract
from jitx.placement import Placement
from jitx.shapes.primitive import Circle
from jitx.test import TestCase
from jitx.via import Via
from jitxlib.jlcpcb import JLC02076_RO4350B
from jitxlib.parts import Capacitor, Inductor

from jitxexamples.components.connectors.wurth_elektronik_60312202114514 import (
    Wurth60312202114514,
)
from jitxexamples.jumpstart_kits.js5_diplexer.main import (
    Diplexer,
    DiplexerBoardCircuit,
)
from tests.parts import PartsTestDesign

HALF = 31.75 / 2
"Half the board's side: the runbook's 31.75 mm square, centred."

PORT_OFFSET = 16.00 - HALF
"16.00 mm from the top or left edge, measured from the centre line."

HOLE_DIAMETER = 3.18
HOLE_PITCH = 25.40

GROUND_PAD_LENGTH = 5.0
GROUND_PAD_INNER = 7.1 / 2
GROUND_PAD_OUTER = 9.9 / 2
"""The jack's ground pads in its own frame (origin on the board edge, +x into
the board): the Würth 60312202114514 data sheet's recommended land pattern,
5.0 mm long from the edge, 7.1 mm inner and 9.9 mm outer overall width."""


class JS5TestDesign(Diplexer):
    """The kit's design, resolving passives through the test parts chain."""

    parts = PartsTestDesign.parts
    parts_lock = PartsTestDesign.parts_lock


@cache
def design() -> JS5TestDesign:
    """One shared instantiation; call only inside a TestCase."""
    return JS5TestDesign()


def circuit() -> DiplexerBoardCircuit:
    c = design().circuit
    assert isinstance(c, DiplexerBoardCircuit)
    return c


class TestOutline(TestCase):
    def test_board_is_the_zdplx_square(self) -> None:
        board = design().board
        assert isinstance(board, Board)
        minx, miny, maxx, maxy = board.shape.to_shapely().g.bounds
        for got, want in zip(
            (minx, miny, maxx, maxy), (-HALF, -HALF, HALF, HALF), strict=True
        ):
            self.assertAlmostEqual(got, want, places=6)
        self.assertAlmostEqual(board.shape.to_shapely().g.area, 31.75**2, places=6)

    def test_two_holes_at_opposite_corners(self) -> None:
        holes = list(extract(circuit(), Cutout))
        circles = [h for h in holes if isinstance(h.shape.geometry, Circle)]
        self.assertEqual(len(circles), 2)
        centres = []
        for hole in circles:
            geometry = hole.shape.geometry
            assert isinstance(geometry, Circle)
            self.assertAlmostEqual(geometry.radius * 2, HOLE_DIAMETER, places=6)
            x, y = hole.shape.transform.translation
            centres.append((round(x, 6), round(y, 6)))
        (x0, y0), (x1, y1) = sorted(centres)
        # Top-left and bottom-right, 25.40 mm apart each way.
        self.assertLess(x0, 0)
        self.assertGreater(y0, 0)
        self.assertAlmostEqual(x1 - x0, HOLE_PITCH, places=6)
        self.assertAlmostEqual(y0 - y1, HOLE_PITCH, places=6)
        # Centred on the board, as the case's holes are.
        self.assertAlmostEqual(x0 + x1, 0.0, places=6)
        self.assertAlmostEqual(y0 + y1, 0.0, places=6)


class TestPorts(TestCase):
    def test_a_wurth_jack_on_each_port_edge(self) -> None:
        n = circuit().network
        # (port, jack, origin on the board edge, rotation pointing +x inward)
        expected = (
            ("common", n.j1, (-HALF, -PORT_OFFSET), 0.0),  # left edge
            ("low", n.j2, (PORT_OFFSET, -HALF), 90.0),  # bottom edge
            ("high", n.j3, (HALF, -PORT_OFFSET), 180.0),  # right edge
        )
        for name, jack, (x, y), rotate in expected:
            with self.subTest(jack=name):
                self.assertIsInstance(jack, Wurth60312202114514)
                placement = jack.transform
                self.assertIsInstance(placement, Placement)
                assert placement is not None
                px, py = placement.translation
                self.assertAlmostEqual(px, x, places=6)
                self.assertAlmostEqual(py, y, places=6)
                self.assertAlmostEqual(placement.rotation % 360, rotate, places=6)


class TestFabrication(TestCase):
    def test_on_the_jlcpcb_076_rogers_substrate(self) -> None:
        self.assertIsInstance(design().substrate, JLC02076_RO4350B)

    def test_no_via_is_filled(self) -> None:
        # JLCPCB neither fills nor caps vias on its Rogers boards (the user,
        # 2026-11-11).
        vias = list(extract(circuit(), Via))
        self.assertGreater(len(vias), 0)
        for i, via in enumerate(vias):
            with self.subTest(via=i):
                self.assertFalse(via.filled)

    def test_jack_ground_vias_in_pad_and_open(self) -> None:
        # The runbook puts the board's ground vias in each jack's ground pads;
        # the user left them plated and open: not filled, capped or tented.
        n = circuit().network
        in_pad = [v for v in extract(circuit(), Via) if v.via_in_pad]
        sites: list[tuple[float, float]] = []
        for via in in_pad:
            assert via.transform is not None
            x, y = via.transform.translation
            sites.append((x, y))
        claimed: set[int] = set()
        for name, jack in (("common", n.j1), ("low", n.j2), ("high", n.j3)):
            assert jack.transform is not None
            to_jack = jack.transform.inverse()
            inside = set()
            for i, site in enumerate(sites):
                x, y = to_jack * site
                if (
                    0.0 < x < GROUND_PAD_LENGTH
                    and GROUND_PAD_INNER < abs(y) < GROUND_PAD_OUTER
                ):
                    inside.add(i)
            claimed |= inside
            with self.subTest(jack=name):
                self.assertGreater(len(inside), 0)
        # Every in-pad via sits in a jack's ground pad.
        self.assertEqual(claimed, set(range(len(sites))))
        for i, via in enumerate(in_pad):
            with self.subTest(via=i):
                self.assertFalse(via.filled)
                # Untented on both sides. None covers both, and a Side covers one
                # (Side.Top is the integer 0, equal to False), so compare by
                # identity or as an empty set.
                tented = via.tented
                uncovered = tented is False or (isinstance(tented, set) and not tented)
                self.assertTrue(uncovered, f"tented={tented!r}")


class TestParts(TestCase):
    def test_the_approved_parts(self) -> None:
        # The user-approved part per reference, from the run's final report.
        n = circuit().network
        approved: list[tuple[Capacitor | Inductor, str]] = [
            (n.c1, "04021J0R4ZBSTR"),
            (n.c2, "04021J1R3ZBSTR"),
            (n.c3, "04021J0R9ZBSTR"),
            (n.c4, "04021J0R2ZBSTR"),
            (n.c5, "04021J1R6ZBSTR"),
            (n.c6, "04021J0R8ZBSTR"),
            (n.l1, "LQW15AN3N7G80D"),
            (n.l2, "LQW15AN3N5G80D"),
        ]
        for part, mpn in approved:
            with self.subTest(mpn=mpn):
                self.assertEqual(str(part.mpn), mpn)
                self.assertEqual(
                    part.part.identity.provider, "csv:example-passives.csv"
                )
