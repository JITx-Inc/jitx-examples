"""Checks of the 0826-1G1T-23-F component against Bel Fuse drawing 08261G1T23-F,
revision F.

Pin functions come from the page 2 schematic and LED polarity table; hole
positions and diameters from the page 4 recommended PCB footprint (component
side view), using the drawing's millimetre reference values. The tables below
are transcribed from the drawing here, not imported from the component.
"""

from collections.abc import Sequence

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_lm1117ld.py uses it
# for the same reason).
from jitx._translate.design import package_design
from jitx.circuit import Circuit
from jitx.container import inline
from jitx.feature import Cutout
from jitx.inspect import extract, visit
from jitx.landpattern import Pad, PadMapping
from jitx.net import Net, Port, Provide
from jitx.sample import SampleDesign
from jitx.shapes.primitive import Circle
from jitx.symbol import Pin
from jitx.test import TestCase
from jitxlib.landpatterns.pads import NPTHPad
from jitxlib.protocols.ethernet.mdi.mdi1000base_t import MDI1000BaseT
from jitxlib.protocols.ethernet.mdi.mdi100base_tx import MDI100BaseTX
from jitxlib.symbols.box import BoxSymbol

from jitxexamples.components.connectors.bel_fuse_0826_1G1T_23_F import (
    Bel_0826_1G1T_23_F,
)

# Page 2: device-side pin number -> name as the schematic prints it.
PIN_TABLE: dict[int, str] = {
    1: "TRCT3",
    2: "TRD3-",
    3: "TRD3+",
    4: "TRD2+",
    5: "TRD2-",
    6: "TRCT2",
    7: "TRCT4",
    8: "TRD4+",
    9: "TRD4-",
    10: "TRD1-",
    11: "TRD1+",
    12: "TRCT1",
    13: "LED1-",
    14: "LED1+",
    15: "LED2-",
    16: "LED2+",
}


class JackDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        jack = Bel_0826_1G1T_23_F()


class GigabitDesign(SampleDesign):
    """Takes 1000BASE-T from the jack, as an application does."""

    @inline
    class circuit(Circuit):
        jack = Bel_0826_1G1T_23_F()

        def __init__(self) -> None:
            # A required bundle goes on a net; it is not a field.
            self.mdi = MDI1000BaseT()
            self.link = self.jack.require(MDI1000BaseT) + self.mdi


class FastDesign(SampleDesign):
    """Takes 100BASE-TX from the jack, as an application does."""

    @inline
    class circuit(Circuit):
        jack = Bel_0826_1G1T_23_F()

        def __init__(self) -> None:
            self.mdi = MDI100BaseTX()
            self.link = self.jack.require(MDI100BaseTX) + self.mdi


def expected_port(part: Bel_0826_1G1T_23_F.Component, name: str) -> Port:
    """The component port for a page 2 pin name."""
    if name.startswith("TRCT"):
        return part.TRCT[int(name[4])]
    if name.startswith("TRD"):
        pair = part.TRD[int(name[3])]
        return pair.p if name.endswith("+") else pair.n
    led = name[:4]
    anode = name.endswith("+")
    return {
        ("LED1", True): part.LED1_A,
        ("LED1", False): part.LED1_C,
        ("LED2", True): part.LED2_A,
        ("LED2", False): part.LED2_C,
    }[(led, anode)]


def single_pad(mapping: PadMapping, port: Port) -> Pad:
    pads = mapping[port]
    if isinstance(pads, Sequence):
        if len(pads) != 1:
            raise AssertionError(f"{port} maps to {len(pads)} pads")
        return pads[0]
    return pads


def hole_diameter(item: Pad | NPTHPad) -> float:
    cutouts = list(extract(item, Cutout))
    if len(cutouts) != 1:
        raise AssertionError(f"{item} has {len(cutouts)} cutouts")
    hole = cutouts[0].shape
    if not isinstance(hole, Circle):
        raise AssertionError(f"hole is {hole}, not a circle")
    return 2.0 * hole.radius


def center(item: Pad | NPTHPad) -> tuple[float, float]:
    placement = item.transform
    if placement is None:
        raise AssertionError("pad has no placement")
    x, y = placement.translation
    return x, y


def single_pins(root: object) -> list[Port]:
    """Every port under ``root`` that is one pin, not a bundle of them."""
    return [p for p in extract(root, Port) if not list(extract(p, Port))]


def joined(root: Circuit, a: Port, b: Port) -> bool:
    """Whether one net under ``root`` holds both ports."""
    return any(
        any(p is a for p in net) and any(p is b for p in net)
        for net in extract(root, Net)
    )


def required[T: Port](root: Circuit, bundle: type[T]) -> T:
    """The one ``bundle`` that ``root`` requires from a provider."""
    found = [
        port
        for net in extract(root, Net)
        for port in net.connected
        if isinstance(port, bundle) and Provide.provided_by(port) is not None
    ]
    if len(found) != 1:
        raise AssertionError(f"{len(found)} required {bundle.__name__} bundles")
    return found[0]


def assignments(req: Port, bundle: type[Port]) -> list[dict[int, Port]]:
    """Each way the provider can serve ``req``: for every single pin of
    ``req``, keyed by ``id``, the provider's pin it would land on."""
    provider = Provide.provided_by(req)
    if provider is None:
        raise AssertionError(f"{req} has no provider")
    out: list[dict[int, Port]] = []
    for offer in extract(provider, Provide):
        if not isinstance(offer.bundle, bundle):
            continue
        # The same bundle type lists its pins in the same order.
        corresponding = list(
            zip(single_pins(req), single_pins(offer.bundle), strict=True)
        )
        for option in offer.options:
            target = {id(a): b for a, b in option}
            out.append({id(r): target[id(o)] for r, o in corresponding})
    return out


def page_2_name(part: Bel_0826_1G1T_23_F.Component, port: Port) -> str:
    """The page 2 pin name of one of the component's ports."""
    for name in PIN_TABLE.values():
        if expected_port(part, name) is port:
            return name
    raise AssertionError(f"{port} is not a page 2 pin")


class TestBel0826(TestCase):
    def test_identity(self) -> None:
        part = JackDesign().circuit.jack.J
        self.assertEqual(part.mpn, "0826-1G1T-23-F")
        self.assertEqual(part.manufacturer, "Bel Fuse")
        self.assertEqual(part.reference_designator_prefix, "J")
        self.assertIsNone(part.value)

    def test_pins_match_page_2(self) -> None:
        part = JackDesign().circuit.jack.J
        mapping = part.pad_mapping
        lp = part.landpattern
        for pin, name in PIN_TABLE.items():
            with self.subTest(pin=pin, name=name):
                self.assertIs(single_pad(mapping, expected_port(part, name)), lp.p[pin])
        self.assertIs(single_pad(mapping, part.SHIELD[1]), lp.p[17])
        self.assertIs(single_pad(mapping, part.SHIELD[2]), lp.p[18])

    def test_port_and_pad_counts(self) -> None:
        part = JackDesign().circuit.jack.J
        # 16 leads and 2 shield leads; the two posts are non-plated.
        self.assertEqual(len(single_pins(part)), 18)
        self.assertEqual(sum(1 for _ in visit(part.landpattern, Pad)), 18)
        self.assertEqual(sum(1 for _ in visit(part.landpattern, NPTHPad)), 2)

    def test_hole_diameters(self) -> None:
        lp = JackDesign().circuit.jack.J.landpattern
        for pin in range(1, 13):
            with self.subTest(pin=pin):
                self.assertAlmostEqual(hole_diameter(lp.p[pin]), 0.89, delta=0.01)
        for pin in range(13, 17):
            with self.subTest(pin=pin):
                self.assertAlmostEqual(hole_diameter(lp.p[pin]), 1.02, delta=0.01)
        for pin in (17, 18):
            with self.subTest(pin=pin):
                self.assertAlmostEqual(hole_diameter(lp.p[pin]), 1.57, delta=0.01)
        for post in lp.mounts:
            self.assertAlmostEqual(hole_diameter(post), 3.25, delta=0.01)

    def test_footprint_page_4(self) -> None:
        lp = JackDesign().circuit.jack.J.landpattern
        (lx, ly), (rx, ry) = (center(post) for post in lp.mounts)
        # Posts 12.70 apart, side by side; the datum is their midpoint.
        self.assertAlmostEqual(ly, ry)
        self.assertAlmostEqual(rx - lx, 12.70, delta=0.01)
        ox, oy = (lx + rx) / 2.0, ly

        def at(n: int) -> tuple[float, float]:
            x, y = center(lp.p[n])
            return x - ox, y - oy

        # Rows 15.24, 17.78 and 20.32 behind the posts.
        for pins, behind in (
            (range(1, 7), 15.24),
            (range(7, 13), 17.78),
            (range(13, 17), 20.32),
        ):
            for n in pins:
                with self.subTest(pin=n):
                    self.assertAlmostEqual(at(n)[1], -behind, delta=0.01)
        # 2.03 pitch in rows 1 and 2, left to right in pin order.
        for a, b in ((1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (7, 8), (8, 9)):
            with self.subTest(pins=(a, b)):
                self.assertAlmostEqual(at(b)[0] - at(a)[0], 2.03, delta=0.01)
        for a, b in ((10, 11), (11, 12)):
            with self.subTest(pins=(a, b)):
                self.assertAlmostEqual(at(b)[0] - at(a)[0], 2.03, delta=0.01)
        # Row 2 is offset 1.02 from row 1: pin 9 is 1.02 left of pin 3.
        self.assertAlmostEqual(at(3)[0] - at(9)[0], 1.02, delta=0.01)
        # Rows are centered on the datum.
        self.assertAlmostEqual(at(1)[0] + at(6)[0], 0.0)
        self.assertAlmostEqual(at(7)[0] + at(12)[0], 0.0)
        # LED leads: 13 to 16 span 12.19, 14 to 15 span 7.11; 13 under 7.
        self.assertAlmostEqual(at(16)[0] - at(13)[0], 12.19, delta=0.01)
        self.assertAlmostEqual(at(15)[0] - at(14)[0], 7.11, delta=0.01)
        self.assertAlmostEqual(at(13)[0], at(7)[0])
        self.assertAlmostEqual(at(16)[0], at(12)[0])
        # Shield leads 16.13 apart, 3.17 in front of the posts, 1.71 outboard.
        (sx1, sy1), (sx2, sy2) = at(17), at(18)
        self.assertAlmostEqual(sx2 - sx1, 16.13, delta=0.01)
        self.assertAlmostEqual(sy1, 3.17, delta=0.01)
        self.assertAlmostEqual(sy2, 3.17, delta=0.01)
        self.assertAlmostEqual(lx - ox - sx1, 1.71, delta=0.01)

    def test_circuit_ports_reach_their_pins(self) -> None:
        jack = JackDesign().circuit.jack
        for n in range(1, 5):
            with self.subTest(center_tap=n):
                self.assertTrue(joined(jack, jack.CT[n], jack.J.TRCT[n]))
                for other in range(1, 5):
                    if other != n:
                        self.assertFalse(joined(jack, jack.CT[n], jack.J.TRCT[other]))
        self.assertTrue(joined(jack, jack.LED1.a, jack.J.LED1_A))
        self.assertTrue(joined(jack, jack.LED1.c, jack.J.LED1_C))
        self.assertTrue(joined(jack, jack.LED2.a, jack.J.LED2_A))
        self.assertTrue(joined(jack, jack.LED2.c, jack.J.LED2_C))
        for shield in jack.J.SHIELD.values():
            self.assertTrue(joined(jack, jack.SHIELD, shield))

    def test_symbol_covers_every_port_once(self) -> None:
        part = JackDesign().circuit.jack.J
        box = part.symbol
        self.assertIsInstance(box, BoxSymbol)
        assert isinstance(box, BoxSymbol)
        self.assertEqual(len(list(box.mapping)), len(list(extract(box, Pin))))
        self.assertEqual(
            {id(p) for p in box.mapping}, {id(p) for p in single_pins(part)}
        )

    def test_design_translates(self) -> None:
        packaged = package_design(JackDesign())
        self.assertIsNotNone(packaged.v1)

    def test_1000base_t_pairs_follow_page_2(self) -> None:
        """Pairs A to D land on TRD1 to TRD4, plus on TRDn+ and minus on
        TRDn-. 1000BASE-T's automatic crossover swaps A with B and C with D,
        so the jack also offers those swaps, and no other.
        """
        design = GigabitDesign()
        self.assertIsNotNone(package_design(design).v1)
        part = design.circuit.jack.J
        req = required(design.circuit, MDI1000BaseT)
        offered = {
            frozenset(
                (k, sign, page_2_name(part, option[id(pin)]))
                for k, pair in enumerate(req.TP)
                for sign, pin in (("+", pair.p), ("-", pair.n))
            )
            for option in assignments(req, MDI1000BaseT)
        }
        expected = {
            frozenset(
                (k, sign, f"TRD{trd}{sign}")
                for k, trd in enumerate(order)
                for sign in ("+", "-")
            )
            for order in ((1, 2, 3, 4), (2, 1, 3, 4), (1, 2, 4, 3), (2, 1, 4, 3))
        }
        self.assertEqual(offered, expected)

    def test_100base_tx_on_pairs_a_and_b(self) -> None:
        """100BASE-TX transmits on pair A (TRD1) and receives on pair B
        (TRD2), plus on TRDn+ and minus on TRDn-.
        """
        design = FastDesign()
        self.assertIsNotNone(package_design(design).v1)
        part = design.circuit.jack.J
        req = required(design.circuit, MDI100BaseTX)
        offered = [
            {
                (lane, sign, page_2_name(part, option[id(pin)]))
                for lane, pair in (("TX", req.TX), ("RX", req.RX))
                for sign, pin in (("+", pair.p), ("-", pair.n))
            }
            for option in assignments(req, MDI100BaseTX)
        ]
        expected = {
            ("TX", "+", "TRD1+"),
            ("TX", "-", "TRD1-"),
            ("RX", "+", "TRD2+"),
            ("RX", "-", "TRD2-"),
        }
        self.assertEqual(offered, [expected])
