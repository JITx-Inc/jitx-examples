"""
Texas Instruments NE555 Precision Timer

Component definition for the Texas Instruments NE555 precision timer
in SOIC-8 package.
"""

import jitx
from jitx.net import Port
from jitxlib.landpatterns.generators.soic import SOIC, SOIC_DEFAULT_LEAD_PROFILE
from jitxlib.symbols.box import BoxSymbol, PinGroup, Row


class NE555(jitx.Component):
    mpn = "NE555"
    manufacturer = "Texas Instruments"
    reference_designator_prefix = "U"
    datasheet = "https://www.ti.com/lit/ds/symlink/ne555.pdf"

    GND = Port()
    TRIG = Port()
    OUT = Port()
    RESET = Port()
    CONT = Port()
    THRES = Port()
    DISCH = Port()
    VCC = Port()

    lp = (
        SOIC(num_leads=8)
        .lead_profile(SOIC_DEFAULT_LEAD_PROFILE)
        .narrow(jitx.Toleranced.min_max(4.81, 5.0))
    )

    symb = BoxSymbol(
        rows=Row(
            left=PinGroup(GND, TRIG, OUT, RESET),
            right=PinGroup(VCC, DISCH, THRES, CONT),
        ),
    )


Device: type[NE555] = NE555
