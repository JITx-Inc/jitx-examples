"""
Winbond W25Q128 Serial Flash Memory

Component definition for Winbond W25Q128JVSIQ 128Mbit Serial Flash Memory
"""

from jitx import Toleranced
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.landpattern import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitxlib.landpatterns.generators.soic import SOIC
from jitxlib.landpatterns.leads import LeadProfile, SMDLead
from jitxlib.landpatterns.leads.protrusions import SmallGullWingLeads
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.protocols.serial import WideSPI
from jitxlib.parts import Capacitor


class SymbolW25Q128JVSIQTR(Symbol):
    """Schematic symbol for W25Q128JVSIQ flash memory"""

    pin_name_size = 0.7874
    pad_name_size = 0.7874
    CS_NOT = Pin((-8, 3), 2, Direction.Left)
    DO = Pin((-8, 1), 2, Direction.Left)
    IO2 = Pin((-8, -1), 2, Direction.Left)
    GND = Pin((-8, -3), 2, Direction.Left)
    DI = Pin((8, -3), 2, Direction.Right)
    CLK = Pin((8, -1), 2, Direction.Right)
    IO3 = Pin((8, 1), 2, Direction.Right)
    VCC = Pin((8, 3), 2, Direction.Right)
    reference_designator = Text(">REF", 0.55559, Anchor.C).at((0, 6.27481))
    value_label = Text(">VALUE", 0.55559, Anchor.C).at((0, 5.48741))
    shapes = [
        rectangle(16.00003, 10.80002),
        Circle(radius=0.3).at((-7.00001, 4.40001)),
        Circle(radius=0.3).at((-7.00001, 4.40001)),
    ]


class W25Q128JVSIQ(Component):
    """
    Winbond W25Q128JVSIQ 128Mbit Serial Flash Memory

    Key Specifications:
    - Capacity: 128Mbit (16MB)
    - Interface: Standard/Dual/Quad SPI
    - Voltage: 2.7V to 3.6V
    - Speed: 104MHz max clock
    - Package: SOIC-8 (208mil wide)

    Pin Configuration:
    - CS_NOT: Chip Select (active low)
    - DO: Data Output (MISO/IO1)
    - IO2: I/O2 (WP# in standard SPI, data in Quad SPI)
    - GND: Ground
    - DI: Data Input (MOSI/IO0)
    - CLK: Serial Clock
    - IO3: I/O3 (HOLD# in standard SPI, data in Quad SPI)
    - VCC: Power supply (2.7V to 3.6V)

    Typical Applications:
    - Code storage for MCUs
    - Data logging
    - Firmware updates
    - Configuration storage

    Datasheet: https://www.lcsc.com/datasheet/lcsc_datasheet_1811142111_Winbond-Elec-W25Q128JVSIQ_C97521.pdf
    """

    manufacturer = "Winbond"
    mpn = "W25Q128JVSIQ"
    reference_designator_prefix = "U"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_1811142111_Winbond-Elec-W25Q128JVSIQ_C97521.pdf"

    CS_NOT = Port()
    DO = Port()
    IO2 = Port()
    GND = Port()
    DI = Port()
    CLK = Port()
    IO3 = Port()
    VCC = Port()

    landpattern = (
        SOIC(num_leads=8)
        .lead_profile(
            LeadProfile(
                span=Toleranced.min_max(7.4, 8.0),
                pitch=1.27,
                type=SMDLead(
                    length=Toleranced.min_max(0.4, 1.27),
                    width=Toleranced.min_max(0.31, 0.51),
                    lead_type=SmallGullWingLeads,
                ),
            )
        )
        .package_body(
            RectanglePackage(
                width=Toleranced.min_max(5.2, 5.4),
                length=Toleranced.min_max(5.2, 5.4),
                height=Toleranced.min_max(1.4, 1.75),
            )
        )
    )
    landpattern.model3d = Model3D(
        "winbond_W25Q128JVSIQ.stp",
        position=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
        rotation=(0.0, 0.0, 0.0),
    )

    symbol = SymbolW25Q128JVSIQTR()

    cmappings = [
        SymbolMapping(
            {
                CS_NOT: symbol.CS_NOT,
                DO: symbol.DO,
                IO2: symbol.IO2,
                GND: symbol.GND,
                DI: symbol.DI,
                CLK: symbol.CLK,
                IO3: symbol.IO3,
                VCC: symbol.VCC,
            }
        ),
        PadMapping(
            {
                CS_NOT: [landpattern.p[1]],
                DO: [landpattern.p[2]],
                IO2: [landpattern.p[3]],
                GND: [landpattern.p[4]],
                DI: [landpattern.p[5]],
                CLK: [landpattern.p[6]],
                IO3: [landpattern.p[7]],
                VCC: [landpattern.p[8]],
            }
        ),
    ]


class W25Q128(Circuit):
    """
    W25Q128 128Mbit Serial Flash Memory Reference Circuit

    Features:
    - W25Q128JVSIQ flash memory IC (128Mbit/16MB capacity)
    - 4.7µF bypass capacitor for power supply decoupling
    - SPI interface for communication
    - Proper power and ground connections

    Pin Configuration:
    - CS_NOT: Chip Select (active low)
    - DI: Data Input (MOSI)
    - DO: Data Output (MISO)
    - CLK: Serial Clock
    - IO2: I/O2 (for quad SPI)
    - IO3: I/O3 (for quad SPI)
    - VCC: Power supply (2.7V to 3.6V)
    - GND: Ground

    Datasheet: https://www.lcsc.com/datasheet/lcsc_datasheet_1811142111_Winbond-Elec-W25Q128JVSIQ_C97521.pdf
    """

    # Power supply interface
    power = Power()

    # Quad SPI interface for full 4-wire operation
    qspi = WideSPI.quad(cs=True)

    def __init__(self):
        # Instantiate the W25Q128 flash memory
        self.flash = W25Q128JVSIQ()

        # 4.7µF bypass capacitor for power supply decoupling
        # Using X7R dielectric for good temperature stability
        self.bypass_cap = Capacitor(capacitance=4.7e-6).insert(
            self.flash.VCC, self.flash.GND, short_trace=True
        )

        # Net connections
        nets_list = [
            # Power connections
            self.power.Vp + self.flash.VCC,
            self.power.Vn + self.flash.GND,
            # Quad SPI interface connections
            # Connect all 4 data lines for full quad SPI operation
            self.qspi.data[0] + self.flash.DI,  # Data line 0 (MOSI in standard SPI)
            self.qspi.data[1] + self.flash.DO,  # Data line 1 (MISO in standard SPI)
            self.qspi.data[2] + self.flash.IO2,  # Data line 2 (for quad SPI)
            self.qspi.data[3] + self.flash.IO3,  # Data line 3 (for quad SPI)
            self.qspi.sck + self.flash.CLK,  # Serial Clock
        ]

        # Add chip select connection if available
        if self.qspi.cs is not None:
            nets_list.append(self.qspi.cs + self.flash.CS_NOT)

        self.nets = nets_list


# Device alias for easy import following JITX patterns
Device: type[W25Q128] = W25Q128
