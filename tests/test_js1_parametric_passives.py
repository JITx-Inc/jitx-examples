from jitx.test import TestCase

from jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives.combined import (
    ParametricPassivesShowcase,
)
from jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives.components.panasonic_erj import (
    PanasonicERJ,
)
from jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives.components.samsung_cl import (
    SamsungCL,
)
from jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives.components.vishay_crcw import (
    VishayCRCW,
)
from jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives.components.yageo_rc import (
    YageoRC,
)


class TestParametricPassivesShowcase(TestCase):
    def test_four_families_side_by_side(self):
        design = ParametricPassivesShowcase()
        c = design.circuit
        self.assertIsInstance(c.r_yageo, YageoRC)  # type: ignore
        self.assertIsInstance(c.c_samsung, SamsungCL)  # type: ignore
        self.assertIsInstance(c.r_panasonic, PanasonicERJ)  # type: ignore
        self.assertIsInstance(c.r_vishay, VishayCRCW)  # type: ignore

    def test_live_request_mpns(self):
        # The runbook's step-9 live part request: "49.9 kOhm 0402 1% Yageo and
        # a 100 nF X7R 0603 50 V Samsung CL" — spot-check the generated MPNs
        # against the vendors' part-numbering schemes.
        design = ParametricPassivesShowcase()
        self.assertEqual(design.circuit.r_yageo.mpn, "RC0402FR-0749K9L")  # type: ignore
        self.assertEqual(design.circuit.c_samsung.mpn, "CL10B104KB8NNNC")  # type: ignore

    def test_live_request_value_labels(self):
        # The value label is what a reader sees in the BOM, and it is the one
        # thing pyright, pytest and `jitx build` all ignore. Scaling to an SI
        # prefix divides by a power of ten, so an exact 100 nF part renders as
        # "99.99999999999999 nanofarad" unless the magnitude is rounded back.
        design = ParametricPassivesShowcase()
        self.assertEqual(str(design.circuit.c_samsung.value), "100.0 nanofarad")  # type: ignore
        self.assertEqual(str(design.circuit.r_yageo.value), "49.9 kiloohm")  # type: ignore
