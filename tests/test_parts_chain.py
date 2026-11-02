import csv
import io

from jitx.circuit import Circuit
from jitx.test import TestCase
from jitx.units import F, V, ohm
from jitxlib.parts import AtLeast, Capacitor, Resistor
from jitxlib.parts.error import PartNotFound
from jitxlib.parts.providers import CsvParts

from tests.parts import PartsTestDesign, PlainValueIdeal

# Columns the circuits query with units that `CsvParts` does not add to a bare
# number, so each non-blank cell must carry its own unit ("6.2 GHz").
UNIT_REQUIRED = ("self_resonant_frequency",)


class TwoPassives(Circuit):
    def __init__(self) -> None:
        # The catalogue holds 100 nF 0402 capacitors, so the CSV must answer.
        self.c = Capacitor(capacitance=100e-9 * F, case="0402")
        # The catalogue holds no 1210 resistors, so only `ideal` can answer.
        self.r = Resistor(resistance=4.7e3 * ohm, case="1210")


class RatedCap(Circuit):
    def __init__(self) -> None:
        # The catalogue tops out at 50 V, so only an `ideal` part that ignores
        # the rating could answer this.
        self.c = Capacitor(capacitance=10e-6 * F, rated_voltage_dc=AtLeast(100 * V))


class RatedDesign(PartsTestDesign):
    def __init__(self) -> None:
        self.circuit = RatedCap()


class ChainDesign(PartsTestDesign):
    def __init__(self) -> None:
        self.circuit = TwoPassives()


class TestPartsChain(TestCase):
    def test_chain_is_catalogue_then_ideal(self) -> None:
        providers = list(PartsTestDesign.parts)
        self.assertEqual(len(providers), 2)
        self.assertIsInstance(providers[0], CsvParts)
        self.assertIsInstance(providers[1], PlainValueIdeal)

    def test_rated_query_never_falls_to_ideal(self) -> None:
        with self.assertRaises(PartNotFound):
            RatedDesign()

    def test_catalogue_answers_first_and_ideal_backstops(self) -> None:
        circuit = ChainDesign().circuit
        assert isinstance(circuit, TwoPassives)
        cap = circuit.c
        res = circuit.r
        # A missing CSV reads as an empty catalogue, which would hand the
        # capacitor to `ideal` and leave its manufacturer unset.
        self.assertIsNotNone(cap.manufacturer)
        self.assertIsNone(res.manufacturer)
        self.assertTrue(str(res.mpn).startswith("IDEAL-"))

    def test_catalogue_cells(self) -> None:
        catalogue = list(PartsTestDesign.parts)[0]
        assert isinstance(catalogue, CsvParts)
        text: str = catalogue.file.read_text(encoding="utf-8")
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertGreater(len(rows), 0)
        for row in rows:
            with self.subTest(mpn=row["mpn"]):
                self.assertIn(row["category"], {"resistor", "capacitor", "inductor"})
                tolerance = row["tolerance"].strip()
                if tolerance:
                    # A ratio or a percentage; a unit such as "0.1 pF" breaks
                    # the relative-tolerance comparison.
                    float(tolerance.removesuffix("%"))
                for column in UNIT_REQUIRED:
                    cell = row[column].strip()
                    if cell:
                        with self.assertRaises(ValueError, msg=f"{column}={cell}"):
                            float(cell)
