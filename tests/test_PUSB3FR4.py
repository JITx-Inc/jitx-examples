"""Nexperia PUSB3FR4 against its datasheet (Product data sheet, 12 July 2018):
Table 1 pinning and the Fig. 17 reflow soldering footprint."""

from jitx.circuit import Circuit
from jitx.container import inline
from jitx.landpattern import Pad
from jitx.net import Port
from jitx.test import TestCase
from jitxlib.parts import CapacitorQuery, ResistorQuery

from jitxexamples.components.digital_isolators.PUSB3FR4 import PUSB3FR4
from tests.parts import PartsTestDesign

# Table 1: pin number per port. Pins 6, 7, 9 and 10 are n.c.
PINNING = {
    "CH1": [1],
    "CH2": [2],
    "GND": [3, 8],
    "CH3": [4],
    "CH4": [5],
    "NC6": [6],
    "NC7": [7],
    "NC9": [9],
    "NC10": [10],
}


class Design(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = PUSB3FR4()


def _pad_numbers(comp: PUSB3FR4, pads: Pad | list[Pad] | tuple[Pad, ...]) -> list[int]:
    by_pad = {id(pad): n for n, pad in comp.landpattern.p.items()}
    seq = [pads] if isinstance(pads, Pad) else list(pads)
    return sorted(by_pad[id(pad)] for pad in seq)


class TestPUSB3FR4(TestCase):
    def test_pinning_matches_table_1(self) -> None:
        comp = Design().circuit.comp
        assert isinstance(comp, PUSB3FR4)
        mapping = comp.mappings[0]
        got = {}
        for port, pads in mapping.items():
            assert isinstance(port, Port)
            name = next(n for n in PINNING if getattr(comp, n) is port)
            assert isinstance(pads, (Pad, list, tuple))
            got[name] = _pad_numbers(comp, pads)
        self.assertEqual(got, PINNING)

    def test_lands_match_fig_17(self) -> None:
        comp = Design().circuit.comp
        assert isinstance(comp, PUSB3FR4)
        # Fig. 17: pitch 0.5, rows 0.3 apart edge to edge, lands 0.475 long, so
        # land centres sit at y = +/-0.3875. Pins 1 to 5 run left to right on
        # the bottom row, pins 10 to 6 left to right on the top row.
        expected = {n: (-1.0 + 0.5 * (n - 1), -0.3875) for n in range(1, 6)}
        expected |= {n: (-1.0 + 0.5 * (10 - n), 0.3875) for n in range(6, 11)}
        for n, (x, y) in expected.items():
            transform = comp.landpattern.p[n].transform
            assert transform is not None
            px, py = transform * (0.0, 0.0)
            self.assertAlmostEqual(px, x, places=6, msg=f"pin {n} x")
            self.assertAlmostEqual(py, y, places=6, msg=f"pin {n} y")
