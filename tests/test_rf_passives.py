"""RF filter passives resolve from the example catalogue to orderable 0402 parts.

Each row is a query a 2-6 GHz filter design would write: a value, the 0402 case
and a tolerance bound, plus C0G where the design wants a ceramic capacitor. The
expected part number is built from the manufacturer's part-number system and is
the one part in its family that meets the bound, or for Accu-P at +/-0.02 pF the
P part the catalogue lists first (below):

- Murata LQW15AN_80, reference specification JELF243A_0100K-01, chapter 3 table
  (B = +/-0.1 nH, C = +/-0.2 nH, G = +/-2%; D = taping on a 180 mm reel).
- Murata GJM1555C1H, per-part reference sheets (W = +/-0.05 pF, F = +/-1%,
  C0G(EIA), DC 50 V; D = 180 mm reel).
- Kyocera AVX Accu-P, TDS-RFM-0032 Rev 2, How to Order and the range table
  (0402, voltage 1 = 100 V, 5 = 50 V or 3 = 25 V (the 9.1 and 10 pF rows),
  J = 0+/-30 ppm/C, Z = +/-0.01 pF or P = +/-0.02 pF for C <= 2.0 pF, B = Accu-P,
  S = lead-free termination, TR = tape and reel). The range table shades 100 V
  for the J dielectric up to 1.8 pF only, so 1.9 pF is a 50 V part. Z carries
  the datasheet footnote
  "Tolerances as tight as ±0.01pF are available. Please consult the factory.",
  and Z parts are poorly stocked, so a design that accepts +/-0.02 pF should get
  the orderable P part. The catalogue lists each value's P row before its Z
  row: CsvParts returns
  the first matching row, so a +/-0.02 pF query picks P and only a +/-0.01 pF
  query reaches Z.
"""

from collections.abc import Callable
from dataclasses import dataclass

from jitx.circuit import Circuit
from jitx.test import TestCase
from jitx.units import F, H, V
from jitxlib.parts import AtLeast, AtMost, Capacitor, Inductor
from jitxlib.parts.error import PartNotFound

from tests.parts import PartsTestDesign

PF = 1e-12 * F
NH = 1e-9 * H

PassivePart = Capacitor | Inductor


@dataclass(frozen=True)
class Case:
    """One filter query and the part its datasheet says answers it."""

    make: Callable[[], PassivePart]
    mpn: str


class OnePart(Circuit):
    def __init__(self, make: Callable[[], PassivePart]) -> None:
        self.part = make()


class OnePartDesign(PartsTestDesign):
    def __init__(self, make: Callable[[], PassivePart]) -> None:
        self.circuit = OnePart(make)


def inductor(nh: float, plus_minus_nh: float | None = None) -> Callable[[], Inductor]:
    """A query bounded by an absolute tolerance, or by 2% when none is given."""
    bound = 0.02 if plus_minus_nh is None else plus_minus_nh / nh
    return lambda: Inductor(inductance=nh * NH, case="0402", tolerance=AtMost(bound))


def thin_film(
    pf: float, plus_minus_pf: float = 0.01, volts: float | None = None
) -> Callable[[], Capacitor]:
    """A capacitor query bounded by an absolute tolerance in pF.

    +/-0.01 pF is the bound only an Accu-P Z part meets; +/-0.02 pF admits P too.
    """
    bound = AtMost(plus_minus_pf / pf)
    if volts is None:
        return lambda: Capacitor(capacitance=pf * PF, case="0402", tolerance=bound)
    return lambda: Capacitor(
        capacitance=pf * PF,
        case="0402",
        tolerance=bound,
        rated_voltage_dc=AtLeast(volts * V),
    )


def thin_film_rated(pf: float, volts: float) -> Callable[[], Capacitor]:
    """A thin-film query at a voltage rating, with no tolerance bound."""
    return lambda: Capacitor(
        capacitance=pf * PF,
        case="0402",
        type="thin_film",
        rated_voltage_dc=AtLeast(volts * V),
    )


def c0g(pf: float, bound: float) -> Callable[[], Capacitor]:
    return lambda: Capacitor(
        capacitance=pf * PF,
        case="0402",
        tolerance=AtMost(bound),
        temperature_coefficient_code="C0G",
    )


CASES: tuple[Case, ...] = (
    # LQW15AN: the run's 6.0 nH part; the smallest value (C is its tightest
    # code); 2.2 nH, where G (+/-0.044 nH) is tighter than B (+/-0.1 nH); 27 nH.
    Case(inductor(6.0, 0.1), "LQW15AN6N0B80D"),
    Case(inductor(1.3, 0.2), "LQW15AN1N3C80D"),
    Case(inductor(2.2), "LQW15AN2N2G80D"),
    Case(inductor(27.0), "LQW15AN27NG80D"),
    # GJM1555: the run's 4.0 pF and 1.0 pF parts; 10 pF, where F (+/-1%) beats
    # the +/-2.5% code; 22 pF, the top of the range.
    Case(c0g(4.0, 0.05 / 4.0), "GJM1555C1H4R0WB01D"),
    Case(c0g(1.0, 0.05 / 1.0), "GJM1555C1H1R0WB01D"),
    Case(c0g(10.0, 0.01), "GJM1555C1H100FB01D"),
    Case(c0g(22.0, 0.01), "GJM1555C1H220FB01D"),
    # Accu-P: the run's 1.1, 0.6 and 0.5 pF parts, and 1.9 pF at 50 V, at
    # +/-0.01 pF (Z); then +/-0.02 pF at 1.1 and 0.6 pF, which P meets and which
    # must pick P ahead of Z.
    Case(thin_film(1.1), "04021J1R1ZBSTR"),
    Case(thin_film(0.6), "04021J0R6ZBSTR"),
    Case(thin_film(0.5), "04021J0R5ZBSTR"),
    Case(thin_film(1.9, volts=50.0), "04025J1R9ZBSTR"),
    Case(thin_film(1.1, 0.02), "04021J1R1PBSTR"),
    Case(thin_film(0.6, 0.02), "04021J0R6PBSTR"),
    # The 1.9 pF thin-film query the negative test below makes, at the 50 V the
    # range table shades: it resolves, so the type filter matches rows.
    Case(thin_film_rated(1.9, 50.0), "04025J1R9PBSTR"),
)


class TestRfPassives(TestCase):
    def test_filter_queries_resolve_to_the_datasheet_part(self) -> None:
        for case in CASES:
            with self.subTest(mpn=case.mpn):
                circuit = OnePartDesign(case.make).circuit
                assert isinstance(circuit, OnePart)
                part = circuit.part
                self.assertEqual(
                    part.part.identity.provider, "csv:example-passives.csv"
                )
                self.assertEqual(str(part.mpn), case.mpn)

    def test_no_100v_accu_p_at_1_9_pf(self) -> None:
        # The range table leaves the 0402 100 V column unshaded at 1.9 pF, so no
        # thin-film row may claim one, at any tolerance.
        with self.assertRaises(PartNotFound):
            OnePartDesign(thin_film_rated(1.9, 100.0))
