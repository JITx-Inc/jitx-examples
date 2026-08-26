"""NFVI1369 BGA land pattern for the AMD Versal Premium VP1002.

Ground truth
    AM013 "Versal Adaptive SoC Packaging and Pinouts", a living document at a
    stable URL. **Cite by caption, not by number** — the figure and table
    numbers move between editions, and a stale number still resolves, to a
    different package's diagram, which looks entirely plausible. The captions
    below are stable; see ``AM013_MECHANICAL_FIGURE`` and ``AM013_LAND_TABLE``
    for the edition each number below was read from.

    * The figure captioned "Package Dimensions for NFVI1369 (VP1002 and
      VP1052)" — body D/E = 35.00 BASIC, overall height A = 3.43/3.63/3.83,
      ball matrix M = 37, ball pitch e = 0.92 BASIC, ball array extent
      D1/E1 = 33.12 BASIC (= 36 x 0.92), physical ball diameter
      b = 0.50/0.64/0.70.
    * The table captioned "BGA Package Design Rules" — for 0.92 mm pitch the
      maximum PCB solder land (L) diameter is 0.51 mm (NSMD), with a 0.61 mm
      solder-mask opening.

What ``ball_diameter`` means here
    The jitxlib BGA generator's ``ball_diameter`` argument sets the **copper
    land diameter** of the PCB pad, not the physical solder-ball size. We
    therefore pass the design-rule table's 0.51 mm land, not the mechanical
    drawing's 0.64 mm nominal ball -- the two sit near each other in the
    document and only one of them is a PCB dimension. Solder mask and paste
    follow ``SMDPadConfig`` defaults (mask expansion comes from the substrate's
    registration constraints at build time; AM013's 0.61 mm mask-opening target
    is noted for real boards).

Framework boundary
    ``VersalBGA.get_pad`` is the public ``(row, column) -> Pad`` adapter over
    the framework-internal ``_get_pad``, following
    ``jitxexamples.demos.si_bga_optimization.generic_bga``. Rows are
    zero-indexed in BGA letter order (A=0 ... AU=36, skipping I/O/Q/S/X/Z);
    columns are zero-indexed too, matching the generated coordinates (A1 = ``get_pad(0, 0)``);
    the framework's 1-based column offset lives inside the adapter.
"""

from dataclasses import dataclass

from jitx import Toleranced
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig


# Where the numbers below were read from. Caption first, because AM013 renumbers
# its figures between editions: the mechanical drawing was Figure 246 in v1.9 and
# Figure 273 in v1.10, where Figure 246 is now a *different* package's diagram.
# Re-locate by grepping the caption, then update the number and edition here.
AM013_MECHANICAL_FIGURE = (
    'AM013 "Package Dimensions for NFVI1369 (VP1002 and VP1052)" '
    "-- Figure 246 in v1.9 (May 8, 2026) p.297; Figure 273 in v1.10 p.330"
)
AM013_LAND_TABLE = (
    'AM013 "BGA Package Design Rules" -- Table 34 in v1.9 p.376, unchanged in v1.10'
)


@dataclass(frozen=True)
class PackageSpec:
    """One Versal package option, as read from AM013."""

    code: str
    num_rows: int
    num_cols: int
    pitch: float
    land_diameter: float
    body_size: float
    height_min: float
    height_max: float


NFVI1369 = PackageSpec(
    code="nfvi1369",
    num_rows=37,  # mechanical drawing: M = 37 (ball matrix size)
    num_cols=37,
    pitch=0.92,  # mechanical drawing: e = 0.92 BASIC
    land_diameter=0.51,  # land table: max PCB solder land, 0.92 mm pitch
    body_size=35.0,  # mechanical drawing: D/E = 35.00 BASIC
    height_min=3.43,  # mechanical drawing: A min
    height_max=3.83,  # mechanical drawing: A max
)


class VersalBGA(BGA):
    """Stock BGA generator plus a public pad-lookup adapter."""

    def get_pad(self, row: int, column: int):
        """Public ``(row, column) -> Pad`` lookup, both zero-indexed.

        Takes the same coordinates the generated module carries, so ball
        "A1" is ``get_pad(0, 0)``. The framework numbers columns from 1;
        that ``+ 1`` lives here and nowhere else, which is the point of
        the adapter — a caller-side conversion would put the same
        off-by-one at every call site. Also wraps the framework-internal
        ``_get_pad`` so design code stays clear of leading-underscore
        access and of the numbering mixin's row-letter attribute layout.
        """
        return self._get_pad(row, column + 1)


def make_landpattern(spec: PackageSpec = NFVI1369) -> VersalBGA:
    """Build the land pattern for a full-grid Versal BGA package."""
    return (
        VersalBGA(
            num_rows=spec.num_rows,
            num_cols=spec.num_cols,
            pitch=spec.pitch,
            ball_diameter=spec.land_diameter,
        )
        .pad_config(SMDPadConfig())
        .package_body(
            RectanglePackage(
                width=Toleranced.exact(spec.body_size),
                length=Toleranced.exact(spec.body_size),
                height=Toleranced.min_max(spec.height_min, spec.height_max),
            )
        )
    )
