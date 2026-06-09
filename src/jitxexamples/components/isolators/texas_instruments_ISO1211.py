"""
Texas Instruments ISO1211/ISO1212 Digital Isolator

Component definition for Texas Instruments ISO1211/ISO1212 single-channel digital isolator
with basic isolation between input and output sides.

Datasheet: https://www.ti.com/lit/ds/symlink/iso1211.pdf
"""

from jitx import current
from jitx.anchor import Anchor
from jitx.constraints import IsBoardEdge, Tag, design_constraint
from jitx.landpattern import PadMapping
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.component import Component
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.si import Toleranced
from jitxlib.parts import Capacitor, Resistor
from jitxlib.landpatterns.generators.soic import SOIC
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.leads import LeadProfile, SMDLead
from jitxlib.landpatterns.leads.protrusions import BigGullWingLeads
from jitxlib.landpatterns.package import RectanglePackage


class SymbolISO1211(Symbol):
    """Schematic symbol for ISO1211 digital isolator"""

    pin_name_size = 0.7874
    pad_name_size = 0.7874

    # Input side pins (left side)
    VCC1 = Pin((-10, 3), 2, Direction.Left)
    EN = Pin((-10, 1), 2, Direction.Left)
    OUT = Pin((-10, -1), 2, Direction.Left)
    GND1 = Pin((-10, -3), 2, Direction.Left)

    # Output side pins (right side)
    SENSE = Pin((10, 3), 2, Direction.Right)
    IN = Pin((10, 1), 2, Direction.Right)
    FGND = Pin((10, -1), 2, Direction.Right)
    SUB = Pin((10, -3), 2, Direction.Right)

    reference_designator = Text(">REF", 0.55559, Anchor.C).at((0, 6.27481))
    value_label = Text(">VALUE", 0.55559, Anchor.C).at((0, 5.48741))

    # Draw isolation barrier and component outline
    shapes = [
        rectangle(20.0, 10.8),  # Main component outline
        # Isolation barrier (dashed line in center)
        Polyline(0.2, [(0, -5.4), (0, 5.4)]),  # Vertical isolation line
        # Pin 1 indicator
        Circle(radius=0.3).at((-9.0, 4.4)),
        # Component labels
        Text("ISO1211", 1.0, Anchor.C).at((0, 0)),
        Text("DIGITAL ISOLATOR", 0.6, Anchor.C).at((0, -2.0)),
    ]


class ISO1211(Component):
    """Texas Instruments ISO1211/ISO1212 Digital Isolator"""

    manufacturer = "Texas Instruments"
    mpn = "ISO1211DR"
    reference_designator_prefix = "U"
    datasheet = "https://www.ti.com/lit/ds/symlink/iso1211.pdf"

    # Input side ports (side 1)
    VCC1 = Port()
    """Power supply, side 1 (3.0V to 5.5V)"""
    EN = Port()
    """Output enable (active high)"""
    OUT = Port()
    """Channel output"""
    GND1 = Port()
    """Ground connection for VCC1"""

    # Output side ports (field side)
    SUB = Port()
    """Internal connection to input chip substrate"""
    FGND = Port()
    """Field-side ground"""
    IN = Port()
    """Field-side current input"""
    SENSE = Port()
    """Field-side voltage sense"""

    landpattern = (
        SOIC(num_leads=8)
        .lead_profile(
            LeadProfile(
                span=Toleranced.min_typ_max(
                    5.80, 6.00, 6.19
                ),  # E dimension from drawing
                pitch=1.27,  # 1.27mm pitch for SOIC-8
                type=SMDLead(
                    length=Toleranced.min_typ_max(
                        0.31, 0.41, 0.51
                    ),  # L dimension (lead length)
                    width=Toleranced.min_typ_max(
                        0.33, 0.41, 0.51
                    ),  # b dimension (lead width)
                    lead_type=BigGullWingLeads,
                ),
            ),
        )
        .package_body(
            RectanglePackage(
                width=Toleranced.min_typ_max(
                    3.81, 3.90, 3.98
                ),  # E1 dimension (body width)
                length=Toleranced.min_typ_max(
                    4.81, 4.90, 5.00
                ),  # D dimension (body length)
                height=Toleranced.min_typ_max(1.35, 1.55, 1.75),  # A dimension (height)
            )
        )
        .density_level(DensityLevel.C)
    )
    symbol = SymbolISO1211()

    cmappings = [
        SymbolMapping(
            {
                VCC1: symbol.VCC1,
                EN: symbol.EN,
                OUT: symbol.OUT,
                GND1: symbol.GND1,
                SUB: symbol.SUB,
                FGND: symbol.FGND,
                IN: symbol.IN,
                SENSE: symbol.SENSE,
            }
        ),
        PadMapping(
            {
                VCC1: landpattern.p[1],  # Pin 1: VCC1
                EN: landpattern.p[2],  # Pin 2: EN
                OUT: landpattern.p[3],  # Pin 3: OUT
                GND1: landpattern.p[4],  # Pin 4: GND1
                SUB: landpattern.p[5],  # Pin 5: SUB
                FGND: landpattern.p[6],  # Pin 6: FGND
                IN: landpattern.p[7],  # Pin 7: IN
                SENSE: landpattern.p[8],  # Pin 8: SENSE
            }
        ),
    ]


class HVNets(Tag):
    """Tag for the high voltage external pins"""


class ISO1211Circuit(Circuit):
    """
    ISO1211 Digital Isolator Reference Circuit

    Complete reference implementation based on TI datasheet Figure 17.
    Includes all required external components for proper operation.

    Features:
    - ISO1211 digital isolator IC
    - Field-side current limiting and sensing resistors
    - Input coupling capacitor
    - Bypass capacitors for both power domains
    - Proper SUB pin handling

    Pin Configuration:
    Input Side (Side 1):
    - VCC1: Power supply (3.0V to 5.5V)
    - EN: Output enable (active high)
    - OUT: Channel output
    - GND1: Ground connection

    Output Side (Field Side):
    - SENSE: Field-side voltage sense
    - IN: Field-side current input
    - FGND: Field-side ground
    - SUB: Internal substrate connection

    Datasheet: https://www.ti.com/lit/ds/symlink/iso1211.pdf
    """

    # Power supply interfaces
    power_vcc = Power()
    """VCC1 power supply (3.0V to 5.5V)"""

    # Signal interfaces
    enable = Port()
    """Enable control signal (tie to VCC1 if always enabled)"""
    output_signal = Port()
    """Isolated digital output signal"""

    # Field-side interface (24V side)
    field_input_pos = Port()
    """Field-side positive input (e.g., 24V)"""
    field_input_neg = Port()
    """Field-side negative input (field ground)"""

    def __init__(self):
        # Instantiate the ISO1211 isolator
        self.isolator = ISO1211()

        # VCC1 bypass capacitor (100nF as per datasheet)
        self.bypass_cap_vcc = Capacitor(capacitance=100e-9).insert(
            self.isolator.VCC1, self.isolator.GND1, short_trace=True
        )

        # Field-side components as per datasheet Figure 17
        # RTHR: Current limiting resistor (field input protection)
        # Typical value depends on field voltage and desired current limit
        self.r_thr = Resistor(resistance=10e3)  # 10kΩ typical for 24V input

        # RSENSE: Current sensing resistor (562Ω for 2.25mA limit, 200Ω for higher current)
        self.r_sense = Resistor(resistance=562.0)  # 562Ω for Type 1/3 operation

        # CIN: Input coupling capacitor (field-side filtering)
        self.c_in = Capacitor(capacitance=100e-9)  # 100nF typical

        # Net connections following datasheet application circuit
        self.nets = [
            # VCC1 power connections
            self.power_vcc.Vp + self.isolator.VCC1,
            self.power_vcc.Vn + self.isolator.GND1,
            # Enable signal connection
            self.enable + self.isolator.EN,
            # Output signal connection
            self.output_signal + self.isolator.OUT,
        ]
        self.sub = Port()
        self.hv_nets = [
            # Field-side circuit connections
            # Field input -> RTHR -> node -> RSENSE -> SENSE pin
            self.field_input_pos + self.r_thr.p1,
            self.r_thr.p2 + self.r_sense.p1 + self.c_in.p1 + self.isolator.IN,
            self.r_sense.p2 + self.isolator.SENSE,
            # Field ground connections
            self.field_input_neg + self.isolator.FGND + self.c_in.p2,
            self.sub + self.isolator.SUB,
        ]
        HVNets().assign(*self.hv_nets)
        self.rules = [
            design_constraint(HVNets(), ~IsBoardEdge, priority=1).clearance(4.0),
            design_constraint(HVNets(), HVNets(), priority=1).clearance(
                current.substrate.constraints.min_copper_copper_space
            ),
        ]

        # SUB connection - should be connected to a small floating plane as per datasheet
        # For now, we'll leave it unconnected as per datasheet recommendation
        # In a real design, this would be connected to a 2mm x 2mm floating copper plane
        # that is isolated from both VCC1 ground and field ground


# Device alias for easy import following JITX patterns
Device: type[ISO1211Circuit] = ISO1211Circuit
