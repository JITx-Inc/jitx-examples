from jitx.circuit import Circuit
from jitx.net import Port
from jitx.common import Power
from jitxlib.parts.query_api import Resistor
from ..bjts.BJT_2N3904S_RTKPS import Component as BJT_Component
from ..fets_p_ch.AO6409 import Component as FET_Component


class HighSideSwitch(Circuit):
    """
    High-Side Switch Module
    A circuit that switches a load connected to the positive supply rail
    """

    input = Port()  # Input control signal
    output = Port()  # Output to load
    power = Power()  # Power supply (VDD and GND)

    # Create internal nets
    GND = Port()
    VDD = Port()

    # Net connections for power
    nets = [
        power.Vn + GND,
        power.Vp + VDD,
    ]

    # Input resistor (1kΩ, 1% tolerance)
    r_input = Resistor(
        # description="Input resistor",
        resistance=1000.0,  # 1kΩ
        tolerance=0.01,  # 1%
        case="0603",
    )

    # Internal resistor (10kΩ, 1% tolerance)
    r_int = Resistor(
        # description="Internal resistor",
        resistance=10000.0,  # 10kΩ
        tolerance=0.01,  # 1%
        case="0603",
    )

    # BJT transistor (2N3904S-RTKPS)
    q1 = BJT_Component()

    # PMOS switch (MOS-A06409)
    pmos_sw = FET_Component()

    # Circuit connections
    nets.extend(
        [
            # Input connections
            input + r_input.p1,
            # Power connections
            VDD + r_int.p2,
            GND + q1.E,
            # BJT connections
            r_input.p2 + q1.B,
            q1.C + r_int.p1,
            # PMOS connections
            VDD + pmos_sw.S,  # Source to VDD
            q1.C + pmos_sw.G,  # Gate to BJT collector
            pmos_sw.D0 + output,  # Drain to output
        ]
    )

    def __init__(self):
        super().__init__()
        # Group components for schematic and layout
        self.schematic_group = "high-side-switch-schematic-group"
        self.layout_group = "high-side-switch-layout-group"

    def get_components(self):
        """
        Return list of components for grouping
        """
        return [self.r_input, self.r_int, self.q1, self.pmos_sw]


Device: type[HighSideSwitch] = HighSideSwitch
