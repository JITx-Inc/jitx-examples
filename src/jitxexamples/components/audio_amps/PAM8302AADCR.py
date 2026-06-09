from jitx import PadMapping
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.net import Port
from jitxlib.landpatterns.generators.soic import SOIC
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.leads import LeadProfile, SMDLead
from jitxlib.landpatterns.leads.protrusions import SmallGullWingLeads
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.parts import Capacitor
from jitxlib.symbols.box import BoxSymbol, Row, PinGroup, Column
from jitx.si import Toleranced


class PAM8302AADCR(Component):
    """2.5W Filterless Class-D Mono Audio Amplifier"""

    mpn = "PAM8302AADCR"
    reference_designator_prefix = "U"

    # Audio amplifier pins
    SD = Port()  # Shutdown pin (active low)
    NC = Port()  # No connect
    IN_plus = Port()  # Positive input
    IN_minus = Port()  # Negative input
    VO_plus = Port()  # Positive output
    VDD = Port()  # Power supply
    GND = Port()  # Ground
    VO_minus = Port()  # Negative output

    landpattern = (
        SOIC(num_leads=8)
        .lead_profile(
            LeadProfile(
                span=Toleranced(6.0, 0.2),  # Typical span for SO-8
                pitch=1.27,  # Standard 1.27mm pitch
                type=SMDLead(
                    length=Toleranced(0.835, 0.435),  # Range 0.4-1.27mm
                    width=Toleranced(0.41, 0.1),  # Range 0.31-0.51mm
                    lead_type=SmallGullWingLeads,
                ),
            )
        )
        .package_body(
            RectanglePackage(
                width=Toleranced(3.9, 0.1),  # Typical body width
                length=Toleranced(4.9, 0.1),  # Typical body length
                height=Toleranced(1.55, 0.2),  # Range 1.35-1.75mm
            )
        )
        .density_level(DensityLevel.A)
    )
    symbol = BoxSymbol(
        rows=[
            Row(left=[PinGroup([IN_plus, IN_minus])], bottom_margin=4.0),
            Row(left=[PinGroup([SD, NC])], right=[PinGroup([VO_plus, VO_minus])]),
        ],
        columns=[
            Column(up=[PinGroup([VDD])], down=[PinGroup([GND])]),
        ],
    )

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                SD: [landpattern.p[1]],  # Shutdown pin to pad 1
                NC: [landpattern.p[2]],  # No connect to pad 2
                IN_plus: [landpattern.p[3]],  # Positive input to pad 3
                IN_minus: [landpattern.p[4]],  # Negative input to pad 4
                VO_plus: [landpattern.p[5]],  # Positive output to pad 5
                VDD: [landpattern.p[6]],  # Power supply to pad 6
                GND: [landpattern.p[7]],  # Ground to pad 7
                VO_minus: [landpattern.p[8]],  # Negative output to pad 8
            }
        ),
    ]

    # Property for datasheet URL
    datasheet = "https://www.diodes.com/datasheet/download/PAM8302A.pdf"


class PAM8302AADCRCircuit(Circuit):
    power = Power()
    SD = Port()
    IN_plus = Port()
    IN_minus = Port()
    VO_plus = Port()
    VO_minus = Port()

    def __init__(self):
        self.amp = PAM8302AADCR()

        self.nets = [
            self.power.Vp + self.amp.VDD,
            self.power.Vn + self.amp.GND,
            self.SD + self.amp.SD,
            self.IN_plus + self.amp.IN_plus,
            self.IN_minus + self.amp.IN_minus,
            self.VO_plus + self.amp.VO_plus,
            self.VO_minus + self.amp.VO_minus,
        ]

        # Bypass Capacitors (1uF and 10uF)
        self.c1 = Capacitor(capacitance=1e-6).insert(
            self.amp.VDD, self.amp.GND, short_trace=True
        )
        self.c2 = Capacitor(capacitance=10e-6).insert(
            self.amp.VDD, self.amp.GND, short_trace=True
        )

        self.amp.NC.no_connect()


Device: type[PAM8302AADCRCircuit] = PAM8302AADCRCircuit
