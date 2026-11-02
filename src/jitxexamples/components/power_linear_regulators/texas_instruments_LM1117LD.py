"""
Texas Instruments LM1117LD-ADJ Low Dropout Linear Regulator

Component definition for the adjustable-output LM1117 (LM1117LD-ADJ/NOPB), an
800 mA low dropout linear regulator in the 8-pin WSON (NGN) package.

Pin functions follow Table 6-1 and Figure 6-5 of the LM1117 datasheet
(SNOS412Q). The lead lands are generated from its NGN0008A package outline;
the exposed pad and its paste follow the example board layout and example
stencil design. The datasheet asks for an output
capacitor with 0.3 to 22 ohm ESR and sizes it as tantalum (section 9.2.2.1.3);
a typical ceramic capacitor's ESR is below that range.
"""

import shapely

import jitx
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.shapely import ShapelyGeometry
from jitxlib.landpatterns.generators.son import SON, SONLead
from jitxlib.landpatterns.leads import LeadProfile
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row

# NGN0008A example stencil design: four 0.98 x 1.31 mm openings on the exposed
# pad, centered 0.59 mm and 0.755 mm off its axes, for 78% paste coverage.
THERMAL_PAD_PASTE = ShapelyGeometry(
    shapely.unary_union(
        [
            rectangle(0.98, 1.31).at(x, y).to_shapely().g
            for x in (-0.59, 0.59)
            for y in (-0.755, 0.755)
        ]
    )
)


class LM1117LD(jitx.Component):
    mpn = "LM1117LD-ADJ/NOPB"
    manufacturer = "Texas Instruments"
    reference_designator_prefix = "U"
    datasheet = "https://www.ti.com/lit/ds/symlink/lm1117.pdf"

    ADJ = Port()
    OUT = Port()
    IN = Port()
    NC = Port()

    landpattern = (
        SON(num_leads=8)
        .lead_profile(
            LeadProfile(
                # NGN0008A does not dimension the lead span. Its outline drawing
                # places the lead tips about 0.1 mm inside the 4.0 mm body, so the
                # outer lead edges sit about 3.8 mm apart, which agrees with the
                # example board layout's lands centered 3.3 mm apart. The body's
                # 0.1 mm tolerance is applied.
                span=jitx.Toleranced.min_max(3.7, 3.9),
                pitch=0.8,
                type=SONLead(
                    length=jitx.Toleranced.min_max(0.4, 0.6),
                    width=jitx.Toleranced.min_max(0.25, 0.35),
                ),
            )
        )
        .package_body(
            RectanglePackage(
                width=jitx.Toleranced.min_max(3.9, 4.1),
                length=jitx.Toleranced.min_max(3.9, 4.1),
                height=jitx.Toleranced.min_max(0.0, 0.8),
            )
        )
        .thermal_pad(
            shape=rectangle(2.2, 3),
            config=SMDPadConfig(paste=THERMAL_PAD_PASTE),
        )
    )

    symbol = BoxSymbol(
        rows=Row(
            left=PinGroup(IN),
            right=PinGroup(OUT),
        ),
        columns=Column(
            up=PinGroup(NC),
            down=PinGroup(ADJ),
        ),
    )

    mappings = [
        jitx.PadMapping(
            {
                ADJ: landpattern.p[1],
                IN: [landpattern.p[2], landpattern.p[3], landpattern.p[4]],
                OUT: [
                    landpattern.p[5],
                    landpattern.p[6],
                    landpattern.p[7],
                    landpattern.thermal_pads[0],
                ],
                NC: landpattern.p[8],
            }
        )
    ]


Device: type[LM1117LD] = LM1117LD
