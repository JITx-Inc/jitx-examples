"""
Texas Instruments OPA189 Zero-Drift Operational Amplifier

Component definition for the Texas Instruments OPA189 zero-drift
operational amplifier in SOT23-5 package.
"""

import jitx

from jitx.net import Port
from jitxlib.landpatterns.leads import LeadProfile
from jitxlib.symbols.opamp import OpAmpSymbol
from jitxlib.landpatterns.generators.sot import (
    SOT23_5,
    SOTLead,
)


class OPA189DBV(jitx.Component):
    mpn = "OPA189DBV"
    manufacturer = "Texas Instruments"
    reference_designator_prefix = "U"
    datasheet = "https://www.ti.com/lit/ds/symlink/opa189.pdf"

    INp = Port()
    INn = Port()
    Vp = Port()
    Vn = Port()
    OUT = Port()

    landpattern = SOT23_5().lead_profile(
        LeadProfile(
            span=jitx.Toleranced.min_max(2.6, 3.0),
            pitch=0.95,
            type=SOTLead(
                length=jitx.Toleranced.min_max(0.3, 0.6),
                width=jitx.Toleranced.min_max(0.3, 0.5),
            ),
        )
    )

    symbol = OpAmpSymbol()

    mappings = [
        jitx.PadMapping(
            {
                INn: landpattern.p[1],
                Vn: landpattern.p[2],
                OUT: landpattern.p[3],
                Vp: landpattern.p[4],
                INp: landpattern.p[5],
            }
        ),
        jitx.SymbolMapping(
            {
                INp: symbol.INp,
                INn: symbol.INn,
                Vp: symbol.Vp,
                Vn: symbol.Vn,
                OUT: symbol.OUT,
            }
        ),
    ]


Device: type[OPA189DBV] = OPA189DBV
