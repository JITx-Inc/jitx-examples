"""Checks of the onsemi NTF6P02T3G P-channel MOSFET.

The pinout (SOT-223, CASE 318E, STYLE 3: pin 1 gate, pin 2 drain, pin 3 source,
pin 4 drain) and the recommended footprint (page 7) come from the onsemi data
sheet NTF6P02T3/D.
"""

from collections.abc import Iterable, Sequence

from jitx.inspect import extract, visit
from jitx.landpattern import Pad, PadMapping, PadShape
from jitx.net import Net, Port
from jitx.symbol import SymbolMapping
from jitx.test import TestCase

from jitxexamples.components.fets_p_ch.NTF6P02T3G import Component, NTF6P02T3G


def single_pad(mapping: PadMapping, port: Port) -> Pad:
    pads = mapping[port]
    if isinstance(pads, Sequence):
        if len(pads) != 1:
            raise AssertionError(f"{port} maps to {len(pads)} pads")
        return pads[0]
    return pads


def pad_mapping(part: Component) -> PadMapping:
    (mapping,) = (m for m in part.mappings if isinstance(m, PadMapping))
    return mapping


def joined(nets: Iterable[Net], port: Port) -> set[int]:
    """The ids of every port and net the nets join to ``port``, ``port``
    included."""
    groups: dict[int, set[int]] = {}

    def join(a: object, b: object) -> None:
        merged = groups.get(id(a), {id(a)}) | groups.get(id(b), {id(b)})
        for member in merged:
            groups[member] = merged

    def walk(net: Net) -> None:
        for member in net.connected:
            join(net, member)
            if isinstance(member, Net):
                walk(member)

    for net in nets:
        walk(net)
    return groups.get(id(port), {id(port)})


class TestNTF6P02T3G(TestCase):
    def test_identity(self) -> None:
        part = Component()
        self.assertEqual(part.manufacturer, "onsemi")
        self.assertEqual(part.mpn, "NTF6P02T3G")
        self.assertEqual(part.reference_designator_prefix, "Q")
        self.assertEqual(
            part.datasheet, "https://www.onsemi.com/pdf/datasheet/ntf6p02t3-d.pdf"
        )
        # A MOSFET has no value to print; the BOM names it by its part number.
        self.assertIsNone(part.value)

    def test_landpattern_matches_the_recommended_footprint(self) -> None:
        lp = Component().landpattern
        # Three leads and the tab.
        self.assertEqual(sum(1 for _ in visit(lp, Pad)), 4)
        # Lead pads 1.50 x 2.00 at 2.30 pitch; the 3.80 x 2.00 tab pad 6.30
        # center to center from the lead row.
        for n, (x, y, w, h) in {
            1: (-2.30, -3.15, 1.50, 2.00),
            2: (0.0, -3.15, 1.50, 2.00),
            3: (2.30, -3.15, 1.50, 2.00),
            4: (0.0, 3.15, 3.80, 2.00),
        }.items():
            with self.subTest(pad=n):
                pad = lp.p[n]
                shape = (
                    pad.shape.shape if isinstance(pad.shape, PadShape) else pad.shape
                )
                lox, loy, hix, hiy = shape.to_shapely().bounds
                self.assertAlmostEqual(hix - lox, w)
                self.assertAlmostEqual(hiy - loy, h)
                placement = pad.transform
                assert placement is not None
                px, py = placement.translation
                self.assertAlmostEqual(px, x)
                self.assertAlmostEqual(py, y)

    def test_pins_map_to_style_3_pads(self) -> None:
        part = Component()
        mapping = pad_mapping(part)
        lp = part.landpattern
        self.assertIs(single_pad(mapping, part.G), lp.p[1])
        self.assertIs(single_pad(mapping, part.D[0]), lp.p[2])
        self.assertIs(single_pad(mapping, part.S), lp.p[3])
        # The tab is the drain.
        self.assertIs(single_pad(mapping, part.D[1]), lp.p[4])
        self.assertEqual(len(part.D), 2)

    def test_symbol_pins_map_to_their_ports(self) -> None:
        part = Component()
        (mapping,) = (m for m in part.mappings if isinstance(m, SymbolMapping))
        symbol = part.symbol
        for port, pin in (
            (part.G, symbol.G),
            (part.S, symbol.S),
            (part.D[0], symbol.D2),
            (part.D[1], symbol.D4),
        ):
            with self.subTest(pin=str(pin)):
                self.assertIs(mapping[port], pin)

    def test_wrapper_joins_both_drain_pads_to_d(self) -> None:
        q = NTF6P02T3G()
        nets = list(extract(q, Net))
        part = q.mosfet
        ports = {id(p) for p in (q.d, q.g, q.s, part.G, part.S, *part.D)}
        groups = {
            "d": (q.d, {id(q.d), id(part.D[0]), id(part.D[1])}),
            "g": (q.g, {id(q.g), id(part.G)}),
            "s": (q.s, {id(q.s), id(part.S)}),
        }
        for name, (port, expected) in groups.items():
            with self.subTest(port=name):
                self.assertEqual(joined(nets, port) & ports, expected)
