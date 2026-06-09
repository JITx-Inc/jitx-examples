"""
Analog Devices LT1763 Low Dropout Linear Regulator

Component and circuit definitions for the Analog Devices LT1763 series
low dropout linear regulators with complete application circuit.
"""

from jitx.anchor import Anchor
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.landpattern import PadMapping
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Text
from jitx.si import Toleranced
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitxlib.landpatterns.generators.soic import SOIC
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.leads import LeadProfile, SMDLead
from jitxlib.landpatterns.leads.protrusions import BigGullWingLeads
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.parts import Capacitor


class SymbolLT1763CS8(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    OUT = Pin((-11, 3), 2, Direction.Left)
    SENSE_ADJ = Pin((-11, 1), 2, Direction.Left)
    GND0 = Pin((-11, -1), 2, Direction.Left)
    BYP = Pin((-11, -3), 2, Direction.Left)
    SHDN_NOT = Pin((11, -3), 2, Direction.Right)
    GND1 = Pin((11, -1), 2, Direction.Right)
    GND2 = Pin((11, 1), 2, Direction.Right)
    IN = Pin((11, 3), 2, Direction.Right)

    reference_designator = Text(">REF", 0.55559, Anchor.C).at((0, 5.87481))
    value_label = Text(">VALUE", 0.55559, Anchor.C).at((0, 5.08741))
    shapes = [rectangle(22, 10), Circle(radius=0.3).at((-10, 4))]


class LT1763CS8(Component):
    """
    Analog Devices LT1763 Low Dropout Linear Regulator

    Parametric component supporting multiple output voltages:
    - 1.5V, 1.8V, 2.5V, 3.0V, 3.3V, 5.0V

    Features:
    - Low dropout voltage: 300mV @ 500mA
    - Output current: 500mA
    - Input voltage range: 1.8V to 20V
    - Shutdown control
    - Thermal protection
    """

    OUT = Port()
    """Regulated output voltage"""
    SENSE_ADJ = Port()
    """Remote sense/adjust pin"""
    GND0 = Port()
    """Ground pin 1"""
    BYP = Port()
    """Bypass pin for internal reference"""
    SHDN_NOT = Port()
    """Shutdown control (active low)"""
    GND1 = Port()
    """Ground pin 2"""
    GND2 = Port()
    """Ground pin 3"""
    IN = Port()
    """Input voltage"""

    def __init__(self, output_voltage: float):
        """
        Initialize LT1763 with specified output voltage

        Args:
            output_voltage: Output voltage in volts (1.5, 1.8, 2.5, 3.0, 3.3, or 5.0)
        """
        super().__init__()

        # Voltage to MPN mapping
        voltage_mpn_map = {
            1.5: "LT1763CS8-1.5#TRPBF",
            1.8: "LT1763CS8-1.8#TRPBF",
            2.5: "LT1763CS8-2.5#TRPBF",
            3.0: "LT1763CS8-3#TRPBF",
            3.3: "LT1763CS8-3.3#TRPBF",
            5.0: "LT1763CS8-5#TRPBF",
        }

        if output_voltage not in voltage_mpn_map:
            raise ValueError(
                f"Unsupported output voltage: {output_voltage}V. Supported voltages: {list(voltage_mpn_map.keys())}"
            )

        self.output_voltage = output_voltage
        self.manufacturer = "Analog Devices"
        self.mpn = voltage_mpn_map[output_voltage]
        self.reference_designator_prefix = "U"
        self.datasheet = "https://www.analog.com/media/en/technical-documentation/data-sheets/1763fa.pdf"

        # Landpattern using SOIC generator
        self.landpattern = (
            SOIC(num_leads=8)
            .lead_profile(
                LeadProfile(
                    span=Toleranced.min_typ_max(
                        5.79, 6.00, 6.20
                    ),  # E dimension from drawing (5.791-6.197mm)
                    pitch=1.27,  # 1.27mm pitch for SOIC-8
                    type=SMDLead(
                        length=Toleranced.min_typ_max(
                            0.40, 0.50, 0.65
                        ),  # L dimension (lead length)
                        width=Toleranced.min_typ_max(
                            0.35, 0.41, 0.48
                        ),  # b dimension (lead width)
                        lead_type=BigGullWingLeads,
                    ),
                ),
            )
            .package_body(
                RectanglePackage(
                    width=Toleranced.min_typ_max(
                        3.81, 3.90, 3.99
                    ),  # E1 dimension (body width) from drawing
                    length=Toleranced.min_typ_max(
                        4.80, 4.90, 5.00
                    ),  # D dimension (body length) from drawing
                    height=Toleranced.min_typ_max(
                        1.35, 1.55, 1.75
                    ),  # A dimension (height, typical SOIC-8)
                )
            )
            .density_level(DensityLevel.C)
        )

        self.symbol = SymbolLT1763CS8()

        self.symbolmapping = SymbolMapping(
            {
                self.OUT: self.symbol.OUT,
                self.SENSE_ADJ: self.symbol.SENSE_ADJ,
                self.GND0: self.symbol.GND0,
                self.BYP: self.symbol.BYP,
                self.SHDN_NOT: self.symbol.SHDN_NOT,
                self.GND1: self.symbol.GND1,
                self.GND2: self.symbol.GND2,
                self.IN: self.symbol.IN,
            }
        )
        self.padmapping = PadMapping(
            {
                self.OUT: self.landpattern.p[1],
                self.SENSE_ADJ: self.landpattern.p[2],
                self.GND0: self.landpattern.p[3],
                self.BYP: self.landpattern.p[4],
                self.SHDN_NOT: self.landpattern.p[5],
                self.GND1: self.landpattern.p[6],
                self.GND2: self.landpattern.p[7],
                self.IN: self.landpattern.p[8],
            }
        )


class LT1763LDO(Circuit):
    """
    Parametric LT1763 Low Dropout Linear Regulator Circuit

    Complete LDO circuit with proper input, output, and bypass capacitors
    as recommended in the LT1763 datasheet.

    Features:
    - Input capacitor (Cin): 10µF
    - Output capacitor (Cout): 10µF
    - Bypass capacitor (Cbyp): 0.01µF
    - Parametric input and output voltages
    - Proper voltage ratings (2x expected voltage minimum)
    - Optional shutdown control

    Args:
        input_voltage: Expected input voltage in volts
        output_voltage: Desired output voltage in volts (1.5, 1.8, 2.5, 3.0, 3.3, or 5.0)
        enable_control: If True, exposes shutdown control pin; if False, ties SHDN high
    """

    # Port definitions as class attributes
    power_in = Power()  # Input power: .Vp (VIN), .Vn (GND)
    power_out = Power()  # Output power: .Vp (VOUT), .Vn (GND)
    enable: Port | None = None  # Shutdown control pin (if enable_control=True)

    def __init__(
        self, input_voltage: float, output_voltage: float, enable_control: bool = False
    ):
        """
        Initialize LT1763 LDO circuit

        Args:
            input_voltage: Expected input voltage in volts (must be > output_voltage + 0.3V dropout)
            output_voltage: Desired output voltage in volts (1.5, 1.8, 2.5, 3.0, 3.3, or 5.0)
            enable_control: If True, exposes shutdown control; if False, ties SHDN high internally
        """
        super().__init__()

        # Validate input parameters
        dropout_min = 0.3  # Minimum dropout voltage from datasheet
        if input_voltage < (output_voltage + dropout_min):
            raise ValueError(
                f"Input voltage ({input_voltage}V) too low. Minimum required: {output_voltage + dropout_min}V"
            )

        self.input_voltage = input_voltage
        self.output_voltage = output_voltage
        self.enable_control = enable_control

        # Instantiate the LT1763 regulator
        self.regulator = LT1763CS8(output_voltage)

        # Calculate capacitor voltage ratings (2x expected voltage minimum)
        input_cap_voltage = max(10.0, input_voltage * 2.0)  # Minimum 10V rating
        output_cap_voltage = max(10.0, output_voltage * 2.0)  # Minimum 10V rating
        bypass_cap_voltage = max(
            10.0, output_voltage * 2.0
        )  # Bypass referenced to output

        # Input capacitor: 10µF between VIN and GND
        self.cin = Capacitor(
            capacitance=10e-6,
            rated_voltage=input_cap_voltage,
            temperature_coefficient_code="X7R",  # Stable ceramic for power applications
        ).insert(self.regulator.IN, self.power_in.Vn, short_trace=True)

        # Output capacitor: 10µF between VOUT and GND
        self.cout = Capacitor(
            capacitance=10e-6,
            rated_voltage=output_cap_voltage,
            temperature_coefficient_code="X7R",
        ).insert(self.regulator.OUT, self.power_out.Vn, short_trace=True)

        # Bypass capacitor: 0.01µF between BYP and GND
        self.cbyp = Capacitor(
            capacitance=0.01e-6,
            rated_voltage=bypass_cap_voltage,
            temperature_coefficient_code="C0G",  # Stable for reference bypass
        ).insert(self.regulator.BYP, self.power_out.Vn, short_trace=True)

        # Connect power nets
        self.nets = [
            # Input power connections
            self.power_in.Vp + self.regulator.IN,
            self.power_in.Vn
            + self.power_out.Vn
            + self.regulator.GND0
            + self.regulator.GND1
            + self.regulator.GND2,
            # Output power connections
            self.power_out.Vp + self.regulator.OUT,
            # Connect SENSE to OUT for local sensing (typical application)
            self.regulator.SENSE_ADJ + self.regulator.OUT,
        ]

        # Handle shutdown control
        if enable_control:
            # Expose shutdown control pin
            self.enable = Port()
            """Enable control (active high). Pull low to shutdown regulator."""
            self.nets.append(self.enable + self.regulator.SHDN_NOT)
        else:
            # Tie SHDN high to always enable the regulator
            self.nets.append(self.regulator.SHDN_NOT + self.power_in.Vp)


# Device alias points to the complete LDO circuit
Device: type[LT1763LDO] = LT1763LDO
