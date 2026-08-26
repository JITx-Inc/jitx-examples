"""Import smoke test for the SI BGA optimization demo.

Nothing else in the suite imports ``jitxexamples.demos.*``, so without this the
demo package's imports are never exercised in CI and a bad move or a broken
relative import would go unnoticed. Every module in the package is imported
explicitly for that reason.

This deliberately stops short of instantiating ``bga_optimization_design``,
because instantiation is not portable across the two jitx lines this repo is
currently exposed to:

- **jitx 4.2.x** (public PyPI, what CI resolves): ``PairPoint`` exposes ``pair``,
  which is what ``bga_escape.py`` uses. Instantiation works.
- **jitx 4.3/4.4 pre-releases** (the internal index, what a developer with
  ``PIP_EXTRA_INDEX_URL`` set may get): ``PairPoint`` exposes ``front``/``back``
  instead, so ``bga_escape.py:315`` raises ``AttributeError`` and pyright errors.

The demo is correct for the line CI builds against; it is the *resolution
split* that is the problem, not the code. Once the repo pins which jitx line it
targets, extend this test to instantiate the design and assert on the built
structure.
"""

import unittest

from jitx.sample import SampleDesign

from jitxexamples.demos.si_bga_optimization import (
    bga_escape,
    constraints,
    deskew,
    generic_bga,
    si_geometry,
    substrate,
)


class TestBGAOptimizationDemoImports(unittest.TestCase):
    def test_every_module_imports(self):
        for module in (
            bga_escape,
            constraints,
            deskew,
            generic_bga,
            si_geometry,
            substrate,
        ):
            self.assertTrue(module.__name__.startswith("jitxexamples.demos."))

    def test_build_target_is_a_sample_design(self):
        self.assertTrue(issubclass(bga_escape.bga_optimization_design, SampleDesign))

    def test_lane_geometry_constants_are_consistent(self):
        # The BGA's signal balls must fit inside the declared grid; this is the
        # invariant the escape lanes are derived from.
        signal_balls = 2 * sum(
            len(generic_bga.signal_cols_for_pair(i))
            for i in range(len(generic_bga.SIGNAL_ROW_PAIRS))
        )
        self.assertLess(signal_balls, generic_bga.BGA_ROWS * generic_bga.BGA_COLS)
        for top_row, bottom_row in generic_bga.SIGNAL_ROW_PAIRS:
            self.assertLess(top_row, bottom_row)
            self.assertLess(bottom_row, generic_bga.BGA_ROWS)
