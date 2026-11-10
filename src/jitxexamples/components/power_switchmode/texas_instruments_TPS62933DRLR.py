"""
Texas Instruments TPS62933DRLR
===============================

3.8-V to 30-V, 3-A, 200-kHz to 2.2-MHz, low-IQ synchronous buck converter in
SOT-583 package.
"""

import eseries
from jitx import Circuit, Net
from jitx.anchor import Anchor
from jitx.common import Power
from jitx.component import Component
from jitx.constraints import Tag, design_constraint
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Port, ShortTrace
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitx.units import A, F, H, V, ohm, pct
from jitxlib.parts import (
    AtLeast,
    AtMost,
    Capacitor,
    CapacitorQuery,
    Inductor,
    Resistor,
)


# Option 1: Custom Tags for power nets
class PowerNetTag(Tag):
    """Tag for power nets"""


# Option 2: Simple custom tags for specific nets
class SwTag(Tag):
    """Switch node net"""


class BstTag(Tag):
    """Bootstrap net"""


class RectangleSmdPad(Pad):
    shape = rectangle(0.28, 0.68)
    paste = [
        Paste(rectangle(0.382, 0.782)),
    ]
    soldermask = [
        Soldermask(rectangle(0.382, 0.782)),
    ]


class LandpatternSOT_583_8_L2_1_W1_2_P0_50_LS1_6_BR(Landpattern):
    p = {
        1: RectangleSmdPad().at(Transform((0.64, -0.75), 90)),
        2: RectangleSmdPad().at(Transform((0.64, -0.25), 90)),
        3: RectangleSmdPad().at(Transform((0.64, 0.25), 90)),
        4: RectangleSmdPad().at(Transform((0.64, 0.75), 90)),
        5: RectangleSmdPad().at(Transform((-0.64, 0.75), 90)),
        6: RectangleSmdPad().at(Transform((-0.64, 0.25), 90)),
        7: RectangleSmdPad().at(Transform((-0.64, -0.25), 90)),
        8: RectangleSmdPad().at(Transform((-0.64, -0.75), 90)),
    }

    customlayer = [
        Custom(Text(">VALUE", 0.5, Anchor.W).at((-0.75, 1.9756)), name="Fab"),
        Custom(ArcPolyline(0.06, [Arc((0.8, -1.05), 0.03, 0, -360)]), name="Fab"),
        Custom(ArcPolyline(0.2, [Arc((0.762, -0.762), 0.1, 0, -360)]), name="Fab"),
    ]
    silkscreen = [
        Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 2.9756))),
        Silkscreen(Polyline(0.254, [(0.508, 1.143), (-0.508, 1.143)])),
        Silkscreen(Polyline(0.254, [(-0.508, -1.143), (0.508, -1.143)])),
        Silkscreen(ArcPolyline(0.15, [Arc((0.85, -1.199), 0.075, 0, -360)])),
    ]
    courtyard = [
        Courtyard(rectangle(1.662, 2.54)),
    ]


class SymbolTPS62933DRLR(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    FB = Pin((4, 4), 2, Direction.Right)
    SS = Pin((4, 2), 2, Direction.Right)
    BST = Pin((4, 0), 2, Direction.Right)
    SW = Pin((4, -2), 2, Direction.Right)
    GND = Pin((-6, -2), 2, Direction.Left)
    VIN = Pin((-6, 0), 2, Direction.Left)
    EN = Pin((-6, 2), 2, Direction.Left)
    RT = Pin((-6, 4), 2, Direction.Left)

    shapes = [
        Text(">VALUE", 0.56, Anchor.C).at((0, 6.08741)),
        Text(">REF", 0.56, Anchor.C).at((0, 6.87481)),
        rectangle(10, 10).at(-1, 1),
        Circle(radius=0.3).at(-5, 5),
    ]


class TPS62933DRLR(Component):
    """Step-down type Adjustable 3.8V~30V 3A 0.8V~22V SOT-583  DC-DC Converters ROHS"""

    name = "C3200405"
    manufacturer = "Texas Instruments"
    mpn = "TPS62933DRLR"
    datasheet = "https://wmsc.lcsc.com/wmslc/upload/file/pdf/v2/lcsc/2302220500_Texas-Instruments-TPS62933DRLR_C3200405.pdf"
    reference_designator_prefix = "U"
    landpattern = LandpatternSOT_583_8_L2_1_W1_2_P0_50_LS1_6_BR()

    FB = Port()
    SS = Port()
    BST = Port()
    SW = Port()
    GND = Port()
    VIN = Port()
    EN = Port()
    RT = Port()

    symbol = SymbolTPS62933DRLR()
    mappings = [
        SymbolMapping(
            {
                FB: symbol.FB,
                SS: symbol.SS,
                BST: symbol.BST,
                SW: symbol.SW,
                GND: symbol.GND,
                VIN: symbol.VIN,
                EN: symbol.EN,
                RT: symbol.RT,
            }
        ),
        PadMapping(
            {
                FB: landpattern.p[8],
                SS: landpattern.p[7],
                BST: landpattern.p[6],
                SW: landpattern.p[5],
                GND: landpattern.p[4],
                VIN: landpattern.p[3],
                EN: landpattern.p[2],
                RT: landpattern.p[1],
            }
        ),
    ]


class FeedbackCircuit(Circuit):
    inp = Port()
    out = Port()
    lo = Port()

    def __init__(self, v_in: Toleranced, v_out: Toleranced, current: float) -> None:
        if current <= 0:
            raise ValueError("Feedback-divider current must be positive")
        if v_in.typ <= 0 or v_out.typ <= 0 or v_out.typ >= v_in.typ:
            raise ValueError(
                "Feedback voltage must be positive and below the input voltage"
            )

        low = eseries.find_nearest(eseries.E96, v_out.typ / current)
        high = eseries.find_nearest(eseries.E96, low * (v_in.typ / v_out.typ - 1.0))
        feedback = v_in.typ * low / (high + low)
        if not v_out.in_range(feedback):
            raise ValueError(
                f"Snapped feedback voltage {feedback:g}V is outside {v_out}"
            )

        resistor_query = {
            "case": "0402",
            "mounting": "smd",
            "tolerance": AtMost(1 * pct),
        }
        self.r_hi = Resistor(resistance=high * ohm, **resistor_query)
        self.r_lo = Resistor(resistance=low * ohm, **resistor_query)
        self.IN = self.inp + self.r_hi.p1
        self.FB = self.r_hi.p2 + self.out + self.r_lo.p1
        self.LO = self.r_lo.p2 + self.lo
        self.feedback_voltage = feedback


class TPS62933DRLRCircuit(Circuit):
    """TPS62933 buck converter application circuit.

    EN is left unconnected by default, which the data sheet allows: a floating
    EN pin enables the converter. With ``enable_control=True`` the circuit
    exposes EN as the ``enable`` port instead, for an external divider or
    logic signal to drive.
    """

    vin = Power()
    vout = Power()
    enable: Port | None = None
    """The EN pin, present only when ``enable_control`` is true."""

    def __init__(
        self,
        output_voltage: float = 3.3,
        input_voltage: float = 25.0,
        soft_start: float = 2.0e-3,
        output_current: float = 3.0,
        ripple: float = 50.0e-3,
        debug: bool = False,
        enable_control: bool = False,
    ) -> None:
        self.GND = Net(name="GND")
        self.VOUT = Net(name="VOUT")
        self.VIN = Net(name="VIN")

        self.buck = TPS62933DRLR()
        if enable_control:
            self.enable = Port()
            self.EN = self.enable + self.buck.EN
        else:
            self.buck.EN.no_connect()

        self.VIN += self.vin.Vp + self.buck.VIN
        self.GND += self.buck.GND + self.vin.Vn
        self.RT_res = Resistor(resistance=0 * ohm)
        self.RT_res_short_traces = [
            ShortTrace(self.buck.RT, self.RT_res.p1),
            ShortTrace(self.RT_res.p2, self.buck.GND),
        ]

        self.fb_vdiv_ckt = FeedbackCircuit(
            Toleranced.exact(output_voltage),
            Toleranced.percent(0.800, 3.0),
            0.800 / 10.0e3,
        )
        self.VOUT += self.fb_vdiv_ckt.inp + self.vout.Vp
        self.GND += self.vout.Vn
        self.FB = self.fb_vdiv_ckt.out + self.buck.FB
        self.GND += self.fb_vdiv_ckt.lo

        with CapacitorQuery.require().update(
            type="ceramic", case="0402", tolerance=AtMost(10.0 * pct)
        ):
            self.css = eseries.find_nearest(
                eseries.E12, soft_start * 5.5e-6 / 0.8
            )  # 2.0 ms soft start per datasheet
            self.c_ss = Capacitor(capacitance=(self.css) * F)
            self.c_ss_short_traces = [
                ShortTrace(self.buck.SS, self.c_ss.p1),
                ShortTrace(self.c_ss.p2, self.buck.GND),
            ]

            # Bootstrap circuit: C4 (100nF) between SW and BST through R4 (0Ω) per schematic
            self.cbst = Capacitor(
                capacitance=(0.1e-6) * F,
                rated_voltage_dc=AtLeast(16.0 * V),
                temperature_coefficient_code="X7R",
            )
            self.rbst = Resistor(resistance=(0.0) * ohm)  # R4=0Ω per schematic

        # Create nets for bootstrap circuit connections
        self.SW_NODE = Net(name="SW_NODE")
        self.BST_MID = Net(name="BST_MID")

        # Connect the bootstrap circuit: SW -> C4 -> R4 -> BST
        self.SW_NODE += self.buck.SW + self.cbst.p1  # SW pin to bootstrap cap
        self.BST_MID += self.cbst.p2 + self.rbst.p1  # Bootstrap cap to R4
        self.BST = self.rbst.p2 + self.buck.BST  # R4 to BST pin

        fsw = 1.2e6
        K = float(40.0 * pct)
        L = eseries.find_nearest(
            eseries.E6,
            output_voltage
            / input_voltage
            * (input_voltage - output_voltage)
            / (fsw * K * output_current),
        )

        # Current calculations
        ripple_current = (
            output_voltage
            / input_voltage
            * (input_voltage - output_voltage)
            / (fsw * L)
        )
        peak_current = output_current + ripple_current / 2.0
        rms_current = pow(
            pow(output_current, 2.0) + pow(ripple_current, 2.0) / 12.0, 0.5
        )

        # Additional calculations from comments
        if debug:
            print(
                f"Inductor: L: {L}H, RMS: {rms_current}A, Ripple: {ripple_current}A, Peak: {peak_current}A"
            )
        self.Ind = Inductor(inductance=(L) * H, max_current=AtLeast(output_current * A))
        self.Ind_short_traces = [
            ShortTrace(self.buck.SW, self.Ind.p1),
            ShortTrace(self.Ind.p2, self.vout.Vp),
        ]

        # check for minimum on time and relation to vout/vin ratio
        min_on_time = output_voltage / (input_voltage * fsw)
        if min_on_time < 70.0e-9:
            if debug:
                print(
                    f"Minimum ON time specification violated: {min_on_time} < 70.0e-9"
                )
            raise ValueError(
                f"Minimum ON time specification violated: {min_on_time:.2e}s < 70.0ns. "
                f"Reduce input voltage or increase output voltage."
            )

        # Output capacitance
        D = output_voltage / input_voltage
        cout_min = (
            ripple_current
            / (fsw * ripple * K)
            * ((1.0 - D) * (1.0 + K) + pow(K, 2.0) / 12.0 * (2.0 - D))
        )
        derated_capacitance = cout_min * 3.0

        # Output capacitors
        out_c = 22.0e-6
        with CapacitorQuery.require().update(
            temperature_coefficient_code="X7R",
            rated_voltage_dc=AtLeast(output_voltage * 2.0 * V),
        ):
            min_output_caps = int(derated_capacitance / out_c) + 1

            # Create output capacitors (C6, C7 = 22uF each)
            if debug:
                print(
                    f"Output Cap: count: {min_output_caps} derated-cap: {derated_capacitance} cap:{out_c}"
                )
            self.output_caps = []
            self.output_cap_short_traces = []
            for _ in range(min_output_caps):
                output_cap = Capacitor(case="0805", capacitance=(out_c) * F)
                self.output_caps.append(output_cap)
                self.output_cap_short_traces.extend(
                    [
                        ShortTrace(self.vout.Vp, output_cap.p1),
                        ShortTrace(output_cap.p2, self.buck.GND),
                    ]
                )

            # Additional 100nF output capacitor (C8) per schematic
            self.c_out_100n = Capacitor(case="0402", capacitance=(100.0e-9) * F)
            self.c_out_100n_short_traces = [
                ShortTrace(self.vout.Vp, self.c_out_100n.p1),
                ShortTrace(self.c_out_100n.p2, self.buck.GND),
            ]

        # Input capacitance - 10uF per schematic (C1, C2)
        self.input_caps = []
        self.input_cap_short_traces = []
        with CapacitorQuery.require().update(
            temperature_coefficient_code="X7R",
            rated_voltage_dc=AtLeast(input_voltage * 2.0 * V),
        ):
            for _ in range(2):
                c_inp_reg = Capacitor(capacitance=(10.0e-6) * F)
                self.input_caps.append(c_inp_reg)
                self.input_cap_short_traces.extend(
                    [
                        ShortTrace(self.buck.VIN, c_inp_reg.p1),
                        ShortTrace(c_inp_reg.p2, self.buck.GND),
                    ]
                )

            # Small input cap
            self.c_inp_sm = Capacitor(capacitance=(0.1e-6) * F)
            self.c_inp_sm_short_traces = [
                ShortTrace(self.buck.VIN, self.c_inp_sm.p1),
                ShortTrace(self.c_inp_sm.p2, self.buck.GND),
            ]

        # Feedforward cap - 10pF (marked DNP in schematic)
        with CapacitorQuery.require().update(
            case="0402", temperature_coefficient_code="C0G"
        ):
            self.c_ff = Capacitor(capacitance=(10.0e-12) * F)
            # Across the divider's top resistor: VOUT to FB
            self.VOUT += self.c_ff.p1
            self.FB += self.c_ff.p2
            # Mark as DNP (Do Not Place) per schematic
            self.c_ff.in_bom = False
            self.c_ff.schematic_x_out = True
            self.c_ff.soldered = False

        # Apply tags to nets
        # Option 1: PowerNetTag for VIN and VOUT
        PowerNetTag().assign(self.VIN)
        PowerNetTag().assign(self.VOUT)

        # Option 2: Specific tags for SW_NODE and BST_MID
        SwTag().assign(self.SW_NODE)
        BstTag().assign(self.BST_MID)

        # Design rule constraints
        # 0.25mm clearance for SW_NODE (switch node needs clearance from other nets)
        self.sw_clearance_rule = design_constraint(SwTag(), True).clearance(0.25)

        # 0.25mm clearance for BST_MID (bootstrap node needs clearance from other nets)
        self.bst_clearance_rule = design_constraint(BstTag(), True).clearance(0.25)

        # 0.25mm trace width for VIN and VOUT power nets
        self.power_trace_rule = design_constraint(PowerNetTag()).trace_width(0.25)


Device: type[TPS62933DRLRCircuit] = TPS62933DRLRCircuit
