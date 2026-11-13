"""JS4: Part 4's reference design translates.

Part 4's design starts from Part 3's, which starts from Part 2's and Part 1's,
so one translation runs every part's reference code. What the parts lay out is
checked by runtime builds and live runs of the kit, not here.
"""

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_js2_circuits.py
# uses it for the same reason).
from jitx._translate.design import package_design
from jitx.test import TestCase

from tests.js4_designs import js4_routing_design


class TestPart4Translates(TestCase):
    def test_design_translates(self) -> None:
        packaged = package_design(js4_routing_design())
        self.assertIsNotNone(packaged.v1)
