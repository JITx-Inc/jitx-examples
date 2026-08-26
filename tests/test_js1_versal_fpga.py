"""JS1 Part 3 — tests for the Versal VP1002 reference solution.

Offline invariants for the generated component and the circuit wrapper.
Group-count and spot-check literals are transcribed from the generator's
inventory report and hand-read from the AMD pinout file
(``xcvp1002nfvi1369pkg.txt``); the file itself is NOT required to run this
suite. The one exception is the regeneration-idempotency test, which skips
unless a local copy of the AMD file is present (``JS1_VERSAL_PINOUT`` env
var, or ``.context/versal_vp1002/`` found by walking up from this file).
"""

import hashlib
import os
from functools import cache
from pathlib import Path

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point. Logged under "API
# findings" in internal/kits/js1-stackup-components/TODO.md.
from jitx._translate.design import package_design
from jitx.common import Power
from jitx.inspect import extract
from jitx.landpattern import Pad
from jitx.net import Port
from jitx.test import TestCase

from jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.circuit import (
    GroundDomain,
)
from jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.main import (
    VersalFPGACircuitDesign,
    VersalFPGADesign,
)
from jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.symbols import (
    MAX_PINS_PER_BOX,
)
from jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.tools import (
    generate_pinout as gen,
)
from jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.xcvp1002 import (
    PINOUT_SHA256,
    TOTAL_BALLS,
)

#: Rail sizes from the generator's inventory report (AMD pinout ground truth).
RAIL_SIZES = {
    "GND": 689,
    "GTM_AVCCAUX_L": 2,
    "GTM_AVCCAUX_RN": 2,
    "GTM_AVCC_L": 6,
    "GTM_AVCC_RN": 3,
    "GTM_AVTT_L": 8,
    "GTM_AVTT_RN": 4,
    "GTY_AVCCAUX_RS": 2,
    "GTY_AVCC_RS": 2,
    "GTY_AVTT_RS": 4,
    "NC": 60,
    "RSVDGND": 2,
    "VCCAUX": 6,
    "VCCAUX_PMC": 2,
    "VCCINT": 84,
    "VCCINT_GT_L": 5,
    "VCCINT_GT_R": 3,
    "VCCO_500": 2,
    "VCCO_501": 2,
    "VCCO_502": 2,
    "VCCO_503": 2,
    "VCCO_700": 3,
    "VCCO_701": 3,
    "VCCO_702": 3,
    "VCC_IO": 2,
    "VCC_PMC": 3,
    "VCC_PSFP": 4,
    "VCC_PSLP": 3,
    "VCC_RAM": 6,
    "VCC_SOC": 18,
}

#: Main supply rails the circuit wrapper must tie (SMON and the Kelvin
#: sense pair are separate domains; GND/RSVDGND/NC are not supply rails).
MAIN_RAIL_LABELS = sorted(
    set(RAIL_SIZES) - {"GND", "RSVDGND", "NC"} | {"VCC_BATT", "VCC_FUSE"}
)


@cache
def component_design() -> VersalFPGADesign:
    """One shared instantiation (~7 s); call only inside a TestCase."""
    return VersalFPGADesign()


@cache
def circuit_design() -> VersalFPGACircuitDesign:
    return VersalFPGACircuitDesign()


def _mapped_pads(mapping, port: Port) -> list:
    """Narrow PadMapping's ``Pad | Sequence[Pad]`` lookup to the list form."""
    pads = mapping[port]
    if not isinstance(pads, list):
        raise AssertionError(f"expected a list of pads for {port}")
    return pads


def _find_pinout_file() -> Path | None:
    env = os.environ.get("JS1_VERSAL_PINOUT")
    if env:
        return Path(env)
    rel = Path(".context/versal_vp1002/xcvp1002nfvi1369pkg.txt")
    for parent in Path(__file__).resolve().parents:
        candidate = parent / rel
        if candidate.is_file():
            return candidate
    return None


class TestComponent(TestCase):
    def test_total_ball_count(self):
        fpga = component_design().circuit.fpga  # type: ignore
        ports = list(extract(fpga, Port))
        self.assertEqual(len(ports), TOTAL_BALLS)
        self.assertEqual(len(list(fpga.ball_assignments())), TOTAL_BALLS)
        pads = list(extract(fpga.landpattern, Pad))
        self.assertEqual(len(pads), TOTAL_BALLS)

    def test_group_counts(self):
        fpga = component_design().circuit.fpga  # type: ignore
        rails = [
            (fpga.GND, "GND"),
            (fpga.GTM_AVCCAUX_L, "GTM_AVCCAUX_L"),
            (fpga.GTM_AVCCAUX_RN, "GTM_AVCCAUX_RN"),
            (fpga.GTM_AVCC_L, "GTM_AVCC_L"),
            (fpga.GTM_AVCC_RN, "GTM_AVCC_RN"),
            (fpga.GTM_AVTT_L, "GTM_AVTT_L"),
            (fpga.GTM_AVTT_RN, "GTM_AVTT_RN"),
            (fpga.GTY_AVCCAUX_RS, "GTY_AVCCAUX_RS"),
            (fpga.GTY_AVCC_RS, "GTY_AVCC_RS"),
            (fpga.GTY_AVTT_RS, "GTY_AVTT_RS"),
            (fpga.NC, "NC"),
            (fpga.RSVDGND, "RSVDGND"),
            (fpga.VCCAUX, "VCCAUX"),
            (fpga.VCCAUX_PMC, "VCCAUX_PMC"),
            (fpga.VCCINT, "VCCINT"),
            (fpga.VCCINT_GT_L, "VCCINT_GT_L"),
            (fpga.VCCINT_GT_R, "VCCINT_GT_R"),
            (fpga.VCCO_500, "VCCO_500"),
            (fpga.VCCO_501, "VCCO_501"),
            (fpga.VCCO_502, "VCCO_502"),
            (fpga.VCCO_503, "VCCO_503"),
            (fpga.VCCO_700, "VCCO_700"),
            (fpga.VCCO_701, "VCCO_701"),
            (fpga.VCCO_702, "VCCO_702"),
            (fpga.VCC_IO, "VCC_IO"),
            (fpga.VCC_PMC, "VCC_PMC"),
            (fpga.VCC_PSFP, "VCC_PSFP"),
            (fpga.VCC_PSLP, "VCC_PSLP"),
            (fpga.VCC_RAM, "VCC_RAM"),
            (fpga.VCC_SOC, "VCC_SOC"),
        ]
        self.assertEqual(sorted(RAIL_SIZES), sorted(name for _, name in rails))
        for ports, name in rails:
            with self.subTest(rail=name):
                self.assertEqual(len(ports), RAIL_SIZES[name])
        quads = fpga.gtm_quad_pins()
        self.assertEqual(sorted(quads), [202, 203, 204, 205, 206, 207])

    def test_spot_check_balls(self):
        """Hand-read (ball, port, coordinate) rows from the AMD file."""
        fpga = component_design().circuit.fpga  # type: ignore
        lp = fpga.landpattern
        mapping = fpga.mappings[0]
        quads = fpga.gtm_quad_pins()
        cases = [
            ("A1", fpga.GND[0], (0, 0)),  # grid corner
            ("AU37", fpga.GND[-1], (36, 36)),  # opposite corner
            ("AN35", quads[202].rxp[0], (32, 34)),  # GTM_RXP0_202
            ("B29", quads[207].txn[3], (1, 28)),  # GTM_TXN3_207
            ("F17", fpga.PMC_MIO0_500, (5, 16)),
            ("C10", fpga.LPD_MIO25_502, (2, 9)),
            ("AT10", fpga.IO_L0P_XCC_N0P0_M0P0_700, (35, 9)),
            ("W15", fpga.VP_500, (18, 14)),  # sysmon analog input
            ("AA8", fpga.GTY_REFCLKN0_105, (20, 7)),  # double-letter row
            ("AP6", fpga.IO_L26P_N8P4_M0P52_700, (33, 5)),
        ]
        for ball, port, (row, col) in cases:
            with self.subTest(ball=ball):
                self.assertEqual(gen.ball_to_rc(ball), (row, col))
                pads = _mapped_pads(mapping, port)
                self.assertIs(pads[0], lp.get_pad(row, col))

    def test_symbol_coverage(self):
        fpga = component_design().circuit.fpga  # type: ignore
        partitions = list(fpga.symbol_partitions())
        self.assertEqual(len(fpga.symbols), len(partitions))
        seen: set[int] = set()
        for partition in partitions:
            group = partition.ports()
            self.assertLessEqual(len(group), MAX_PINS_PER_BOX)
            for port in group:
                self.assertNotIn(id(port), seen, "port in two symbol boxes")
                seen.add(id(port))
        all_ports = {id(p) for p in extract(fpga, Port)}
        self.assertEqual(seen, all_ports)

    def test_mapping_bijective(self):
        fpga = component_design().circuit.fpga  # type: ignore
        mapping = fpga.mappings[0]
        pad_ids: set[int] = set()
        for port in extract(fpga, Port):
            pads = _mapped_pads(mapping, port)
            self.assertEqual(len(pads), 1)
            self.assertNotIn(id(pads[0]), pad_ids, "pad mapped twice")
            pad_ids.add(id(pads[0]))
        self.assertEqual(len(pad_ids), TOTAL_BALLS)

    def test_design_translates(self):
        packaged = package_design(component_design())
        self.assertIsNotNone(packaged.v1)


class TestGenerator(TestCase):
    """Pure-function checks; no AMD file, no design context needed."""

    SYNTHETIC = "\n".join(
        [
            "-- Device : xcfake",
            "Pin\tPin Name\tBank\tI/O Type\tSLR\tPerf\tDDRMC",
            "A1\tGND\tNA\tNA\tNA\tNA\tNA",
            "A2\tVCCO_700\t700\tNA\tNA\tNA\tNA",
            "B1\tVCCO_700\t700\tNA\tNA\tNA\tNA",
            "B2\tDONE_503\t503\tPMCDIO\tNA\tNA\tNA",
            "Total Number of Pins 4",
        ]
    )

    def test_box_cap_stays_in_sync(self):
        # The stdlib-only generator restates symbols.MAX_PINS_PER_BOX; the
        # owner enforces it at instantiation, this seals the two constants.
        self.assertEqual(gen.MAX_PINS_PER_BOX, MAX_PINS_PER_BOX)

    def test_ball_ref_round_trip(self):
        for ball, rc in [
            ("A1", (0, 0)),
            ("Y1", (19, 0)),
            ("AA1", (20, 0)),
            ("AU37", (36, 36)),
            ("BB42", (41, 41)),
        ]:
            with self.subTest(ball=ball):
                self.assertEqual(gen.ball_to_rc(ball), rc)
                self.assertEqual(gen.rc_to_ball(*rc), ball)
        with self.assertRaises(ValueError):
            gen.ball_to_rc("I1")  # skipped letter
        with self.assertRaises(ValueError):
            gen.ball_to_rc("A0")  # columns are 1-based

    def test_classifier_rails_vs_uniques(self):
        model = gen.classify(gen.parse_pinout(self.SYNTHETIC, "synthetic"))
        self.assertEqual(set(model.rails), {"VCCO_700"})
        self.assertEqual(set(model.uniques), {"GND", "DONE_503"})

    def test_parse_rejects_bad_totals(self):
        broken = self.SYNTHETIC.replace("Pins 4", "Pins 5")
        with self.assertRaises(ValueError):
            gen.parse_pinout(broken, "synthetic")

    def test_parse_rejects_partial_grid(self):
        # 3 balls on a 2x2 grid extent -> not fully populated.
        partial = self.SYNTHETIC.replace("\nB1\tVCCO_700\t700\tNA\tNA\tNA\tNA", "")
        partial = partial.replace("Pins 4", "Pins 3")
        with self.assertRaises(ValueError):
            gen.parse_pinout(partial, "synthetic")

    def test_regeneration_idempotent(self):
        source = _find_pinout_file()
        if source is None:
            self.skipTest("AMD pinout file not present (maintainer-only check)")
        text = source.read_text()
        sha = hashlib.sha256(text.encode()).hexdigest()
        if sha != PINOUT_SHA256:
            self.skipTest(f"AMD file revision differs (sha256 {sha[:16]}...)")
        committed = (
            Path(__file__).resolve().parents[1]
            / "src/jitxexamples/jumpstart_kits/js1_stackup_components"
            / "versal_fpga/xcvp1002.py"
        )
        model = gen.classify(gen.parse_pinout(text, source.name))
        self.assertEqual(gen.emit_module(model), committed.read_text())


class TestCircuit(TestCase):
    def test_rail_roster(self):
        circ = circuit_design().circuit.fpga_circuit  # type: ignore
        ties = circ.rail_ties()
        main = [t for t in ties if t.domain is GroundDomain.MAIN]
        self.assertEqual(sorted(t.label for t in main), MAIN_RAIL_LABELS)
        sizes = dict(RAIL_SIZES, VCC_BATT=1, VCC_FUSE=1)
        for tie in main:
            with self.subTest(rail=tie.label):
                self.assertEqual(len(tie.pins), sizes[tie.label])
        self.assertEqual(len(circ.rail_nets), len(ties))

    def test_power_port_count(self):
        circ = circuit_design().circuit.fpga_circuit  # type: ignore
        rails = [p for p in extract(circ, Power) if isinstance(p, Power)]
        # 29 main rails + VCCAUX_SMON + VCCINT_SENSE
        self.assertEqual(len(rails), len(MAIN_RAIL_LABELS) + 2)

    def test_ground_domains_distinct(self):
        circ = circuit_design().circuit.fpga_circuit  # type: ignore
        fpga = circ.fpga
        by_domain = {}
        for tie in circ.rail_ties():
            by_domain.setdefault(tie.domain, []).append(tie)
        smon = by_domain[GroundDomain.SMON]
        sense = by_domain[GroundDomain.SENSE]
        self.assertEqual([t.label for t in smon], ["VCCAUX_SMON"])
        self.assertEqual([t.label for t in sense], ["VCCINT_SENSE"])
        self.assertIs(smon[0].pins[0], fpga.VCCAUX_SMON)
        self.assertIs(sense[0].pins[0], fpga.VCCINT_SENSE)
        main_labels = {t.label for t in by_domain[GroundDomain.MAIN]}
        self.assertNotIn("VCCAUX_SMON", main_labels)
        self.assertNotIn("VCCINT_SENSE", main_labels)

    def test_gtm_bundles(self):
        circ = circuit_design().circuit.fpga_circuit  # type: ignore
        self.assertEqual(sorted(circ.gtm), [202, 203, 204, 205, 206, 207])
        for quad in circ.gtm.values():
            self.assertEqual(len(quad.L), 4)
            self.assertEqual(len(quad.REFCLK), 2)
        # 6 quads x (4 lanes x 4 signals + 2 refclks x 2) topology segments
        self.assertEqual(len(circ.gtm_links), 6 * (4 * 4 + 2 * 2))

    def test_circuit_design_translates(self):
        packaged = package_design(circuit_design())
        self.assertIsNotNone(packaged.v1)
