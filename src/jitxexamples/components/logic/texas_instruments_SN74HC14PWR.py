# This file is generated based on the parts database query below:
#    from jitx_parts.query_api import create_part
#    class Example(Circuit) :
#        part = create_part(mpn = "SN74HC14PWR", manufacturer = "Texas Instruments")()

# File Location: components/Texas_Instruments/ComponentSN74HC14PWR.py
# To import this component:
#     from components.Texas_Instruments.ComponentSN74HC14PWR import ComponentSN74HC14PWR
from jitx import Circuit, Polygon
from jitx.anchor import Anchor
from jitx.common import Power
from jitx.component import Component
from jitx.landpattern import PadMapping
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Polyline, Circle, Text
from jitx.si import Toleranced
from jitx.symbol import Symbol, Pin, Direction, SymbolMapping
from jitxlib.landpatterns.generators.sop import SOP
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.leads import LeadProfile, SMDLead
from jitxlib.landpatterns.leads.protrusions import SmallGullWingLeads
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.parts import Capacitor


class SymbolSchmittInverter(Symbol):
    A = Pin((-2, 0), 2, Direction.Left)
    Y = Pin((1, 0), 2, Direction.Right)
    reference_designator = Text(">REF", 0.55559, Anchor.C).at((0, -2.0))
    shapes = [
        # Inverter triangle
        Polygon([(-2, 1.5), (-2, -1.5), (1, 0)]),
        # Inversion bubble at output
        Circle(radius=0.2).at((1.2, 0)),
        # Refined hysteresis symbol - more recognizable square wave
        Polyline(0.1, [(-1.4, -0.3), (-0.8, -0.3), (-0.8, 0.3)]),
        Polyline(0.1, [(-0.6, 0.3), (-1.2, 0.3), (-1.2, -0.3)]),
    ]


class SymbolSN74HC14PWR(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    GND = Pin((-2, -1), 2, Direction.Left)
    VCC = Pin((2, 1), 2, Direction.Right)
    reference_designator = Text(">REF", 0.55559, Anchor.W).at((-2, 2.8))
    value_label = Text(">VALUE", 0.55559, Anchor.W).at((-2, 2.0))
    box = rectangle(4.0, 3.0)


class SN74HC14PWR(Component):
    """Schmitt Trigger 6 21ns@6V,50pF 2uA 2V~6V TSSOP-14  Inverters ROHS"""

    name = "C6821"
    manufacturer = "Texas Instruments"
    mpn = "SN74HC14PWR"
    datasheet = "https://www.ti.com/lit/ds/symlink/sn74hc14.pdf?ts=1763667042597"
    reference_designator_prefix = "U"
    landpattern = (
        SOP(num_leads=14)
        .lead_profile(
            LeadProfile(
                span=Toleranced(6.4, 0.2),  # LS6_4
                pitch=0.65,  # P0_65
                type=SMDLead(
                    length=Toleranced(0.6, 0.15),  # Typical lead length for TSSOP
                    width=Toleranced(0.25, 0.05),  # Typical lead width for TSSOP
                    lead_type=SmallGullWingLeads,
                ),
            )
        )
        .package_body(
            RectanglePackage(
                width=Toleranced(4.4, 0.1),  # W4_4
                length=Toleranced(5.0, 0.1),  # L5_0
                height=Toleranced(1.2, 0.1),  # Typical height
            )
        )
        .density_level(DensityLevel.A)  # Nominal density
    )

    P_1A = Port()
    P_1Y = Port()
    P_2A = Port()
    P_2Y = Port()
    P_3A = Port()
    P_3Y = Port()
    GND = Port()

    P_4Y = Port()
    P_4A = Port()
    P_5Y = Port()
    P_5A = Port()
    P_6Y = Port()
    P_6A = Port()
    VCC = Port()

    symbol = SymbolSN74HC14PWR()
    schmitts = [SymbolSchmittInverter() for _ in range(6)]
    mappings = [
        SymbolMapping(
            {
                P_1A: schmitts[0].A,
                P_1Y: schmitts[0].Y,
                P_2A: schmitts[1].A,
                P_2Y: schmitts[1].Y,
                P_3A: schmitts[2].A,
                P_3Y: schmitts[2].Y,
                GND: symbol.GND,
                P_4Y: schmitts[3].Y,
                P_4A: schmitts[3].A,
                P_5Y: schmitts[4].Y,
                P_5A: schmitts[4].A,
                P_6Y: schmitts[5].Y,
                P_6A: schmitts[5].A,
                VCC: symbol.VCC,
            }
        ),
        PadMapping(
            {
                P_1A: landpattern.p[1],
                P_1Y: landpattern.p[2],
                P_2A: landpattern.p[3],
                P_2Y: landpattern.p[4],
                P_3A: landpattern.p[5],
                P_3Y: landpattern.p[6],
                GND: landpattern.p[7],
                P_4Y: landpattern.p[8],
                P_4A: landpattern.p[9],
                P_5Y: landpattern.p[10],
                P_5A: landpattern.p[11],
                P_6Y: landpattern.p[12],
                P_6A: landpattern.p[13],
                VCC: landpattern.p[14],
            }
        ),
    ]


class SN74HC14PWRCircuit(Circuit):
    power = Power()
    inv = SN74HC14PWR()

    def __init__(self):
        self.nets = [self.inv.GND + self.power.Vn, self.inv.VCC + self.power.Vp]

        self.byp = Capacitor(capacitance=0.1e-6).insert(
            self.inv.VCC, self.inv.GND, short_trace=True
        )


Device: type[SN74HC14PWRCircuit] = SN74HC14PWRCircuit
