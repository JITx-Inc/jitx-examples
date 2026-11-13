"""The chip parts' bodies, from their vendors' drawings.

Board-independent data each part family owns: the nominal body size (the
run's HFSS body models were built at it) and its tolerance, which bounds the
largest body a reel can deliver. ``ChipBody.keepout`` is the region under a
placed part that must hold no copper but the part's own lands
(:py:mod:`.main`, body keepouts).

Frame: a part's land-pattern frame, as ``jitxlib``'s two-pin ``SMT`` draws
it: origin at the body centre, the lands' axis along y, width along x.
"""

from __future__ import annotations

from dataclasses import dataclass

from jitx.shapes import Shape
from jitx.shapes.composites import rectangle
from jitxlib.parts import Capacitor, Inductor

# source: Kyocera AVX Accu-P data sheet (https://datasheets.kyocera-avx.com/accu-p.pdf),
# dimensions table, 0402 column (L)
ACCU_P_LENGTH = 1.00
"""Accu-P 0402 body length, mm."""
# source: Kyocera AVX Accu-P data sheet (https://datasheets.kyocera-avx.com/accu-p.pdf),
# dimensions table, 0402 column (L, 1.00 +/-0.1)
ACCU_P_LENGTH_TOLERANCE = 0.1
"""Accu-P 0402 body length tolerance, mm."""
# source: Kyocera AVX Accu-P data sheet (https://datasheets.kyocera-avx.com/accu-p.pdf),
# dimensions table, 0402 column (W)
ACCU_P_WIDTH = 0.55
"""Accu-P 0402 body width, mm."""
# source: Kyocera AVX Accu-P data sheet (https://datasheets.kyocera-avx.com/accu-p.pdf),
# dimensions table, 0402 column (W, 0.55 +/-0.07)
ACCU_P_WIDTH_TOLERANCE = 0.07
"""Accu-P 0402 body width tolerance, mm."""
# source: Kyocera AVX Accu-P data sheet (https://datasheets.kyocera-avx.com/accu-p.pdf),
# dimensions table, 0402 column (T)
ACCU_P_HEIGHT = 0.40
"""Accu-P 0402 body thickness, mm."""
# source: Kyocera AVX Accu-P data sheet (https://datasheets.kyocera-avx.com/accu-p.pdf),
# dimensions table, 0402 column (B2)
ACCU_P_TERMINATION = 0.20
"""Accu-P 0402 termination length, mm."""

# source: Murata LQW15AN_80 reference specification JELF243A-0100, p8,
# 5. Appearance and Dimensions (1.0 +/-0.1)
LQW15A_LENGTH = 1.0
"""LQW15A body length, mm."""
# source: Murata LQW15AN_80 reference specification JELF243A-0100, p8,
# 5. Appearance and Dimensions (1.0 +/-0.1)
LQW15A_LENGTH_TOLERANCE = 0.1
"""LQW15A body length tolerance, mm."""
# source: Murata LQW15AN_80 reference specification JELF243A-0100, p8,
# 5. Appearance and Dimensions (0.6 +/-0.1)
LQW15A_WIDTH = 0.6
"""LQW15A body width, mm."""
# source: Murata LQW15AN_80 reference specification JELF243A-0100, p8,
# 5. Appearance and Dimensions (0.6 +/-0.1)
LQW15A_WIDTH_TOLERANCE = 0.1
"""LQW15A body width tolerance, mm."""
# source: Murata LQW15AN_80 reference specification JELF243A-0100, p8,
# 5. Appearance and Dimensions (0.5 +/-0.1)
LQW15A_HEIGHT = 0.5
"""LQW15A body height, mm."""
# source: Murata LQW15AN_80 reference specification JELF243A-0100, p8,
# 5. Appearance and Dimensions (0.2 +/-0.1)
LQW15A_TERMINATION = 0.2
"""LQW15A electrode length, mm."""


@dataclass(frozen=True)
class ChipBody:
    """A two-terminal chip body: nominal length (along its lands' axis) and
    width, mm, each with its +/- tolerance."""

    length: float
    length_tolerance: float
    width: float
    width_tolerance: float

    def outline(self) -> tuple[float, float]:
        """The largest body the drawing allows, (width, length), mm."""
        return (self.width + self.width_tolerance, self.length + self.length_tolerance)

    def keepout_reach(self, clearance: float) -> tuple[float, float]:
        """How far the keepout reaches from the body centre, (across, along)
        the lands' axis, mm: half the largest body plus ``clearance``."""
        width, length = self.outline()
        return (width / 2 + clearance, length / 2 + clearance)

    def keepout(self, clearance: float) -> Shape:
        """The largest body grown by ``clearance`` on every side, centred on
        the land-pattern origin, lands' axis along y."""
        across, along = self.keepout_reach(clearance)
        return rectangle(2 * across, 2 * along)


ACCU_P_BODY = ChipBody(
    ACCU_P_LENGTH, ACCU_P_LENGTH_TOLERANCE, ACCU_P_WIDTH, ACCU_P_WIDTH_TOLERANCE
)
"""Kyocera AVX Accu-P 0402 (every capacitor on this board)."""

LQW15A_BODY = ChipBody(
    LQW15A_LENGTH, LQW15A_LENGTH_TOLERANCE, LQW15A_WIDTH, LQW15A_WIDTH_TOLERANCE
)
"""Murata LQW15A (every inductor on this board)."""


def chip_body(part: Capacitor | Inductor) -> ChipBody:
    """The body of a chip part on this board: the capacitors are all Accu-P,
    the inductors all LQW15A (:py:mod:`.network` queries)."""
    return ACCU_P_BODY if isinstance(part, Capacitor) else LQW15A_BODY
