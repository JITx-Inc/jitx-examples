"""
Texas Instruments TPS62933DRLR
===============================

3.8-V to 30-V, 3-A, 200-kHz to 2.2-MHz, low-IQ synchronous buck converter in
SOT-583 package.
"""

import eseries
from jitx import Circuit, Net
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.constraints import Tag, design_constraint
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.landpattern import PadMapping
from jitx.net import Port
from jitx.common import Power
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol
from jitx.symbol import SymbolMapping
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitx.units import ohm, pct
from jitxlib.parts import (
    Capacitor,
    CapacitorQuery,
    Inductor,
    Resistor,
    ResistorQuery,
)
from jitxlib.voltage_divider import (
    VoltageDividerConstraints,
    voltage_divider_from_constraints,
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
    inp: Port
    out: Port
    lo: Port

    def __init__(self, v_in, v_out, current):
        self.inp = Port()
        self.out = Port()
        self.lo = Port()

        self.IN = Net(name="IN")
        self.OUT = Net(name="OUT")
        self.GND = Net(name="GND")

        resQuery = ResistorQuery(mounting="smd", case=["0402"], min_stock=10)
        cons = VoltageDividerConstraints(
            v_in=v_in,
            v_out=v_out,
            current=current,
            prec_series=[1.00, 0.10],
            base_query=resQuery,
        )
        self.sol = voltage_divider_from_constraints(
            cons, name="feedback divider vout -> fb"
        )
        self.IN += self.sol.hi + self.inp
        self.OUT += self.sol.out + self.out
        self.GND += self.sol.lo + self.lo


class TPS62933DRLRCircuit(Circuit):
    vin = Power()
    vout = Power()

    # resQueryDefaults = ResistorQuery(
    #     mounting="smd", case=["0805", "0603", "0402", "0201"]
    # )
    # capQueryDefaults = CapacitorQuery(mounting="smd")
    # indQueryDefaults = InductorQuery(current_rating=5.0)

    def __init__(
        self,
        output_voltage=3.3,
        input_voltage=25.0,
        soft_start=2.0e-3,
        output_current=3.0,
        ripple=50.0e-3,
        debug=False,
    ):
        self.nets = []
        self.GND = Net(name="GND")
        self.VOUT = Net(name="VOUT")
        self.VIN = Net(name="VIN")

        self.buck = TPS62933DRLR()
        self.buck.EN.no_connect()

        self.VIN += self.vin.Vp + self.buck.VIN
        self.GND += self.buck.GND + self.vin.Vn
        self.RT_res = Resistor(resistance=0 * ohm).insert(
            self.buck.RT, self.GND, short_trace=True
        )

        self.fb_vdiv_ckt = FeedbackCircuit(
            Toleranced.exact(output_voltage),
            Toleranced.percent(0.800, 3.0),
            0.800 / 10.0e3,
        )
        self.VOUT += self.fb_vdiv_ckt.inp + self.vout.Vp
        self.GND += self.vout.Vn
        self.nets.append(self.fb_vdiv_ckt.out + self.buck.FB)
        self.GND += self.fb_vdiv_ckt.lo

        with CapacitorQuery.refine(type="ceramic", case="0402", tolerance=10.0 * pct):
            self.css = eseries.find_nearest(
                eseries.E12, soft_start * 5.5e-6 / 0.8
            )  # 2.0 ms soft start per datasheet
            self.c_ss = Capacitor(capacitance=self.css).insert(
                self.buck.SS, self.GND, short_trace=True
            )

            # Bootstrap circuit: C4 (100nF) between SW and BST through R4 (0Ω) per schematic
            self.cbst = Capacitor(
                capacitance=0.1e-6,
                rated_voltage=16.0,
                temperature_coefficient_code="X7R",
            )
            self.rbst = Resistor(resistance=0.0)  # R4=0Ω per schematic

        # Create nets for bootstrap circuit connections
        self.SW_NODE = Net(name="SW_NODE")
        self.BST_MID = Net(name="BST_MID")

        # Connect the bootstrap circuit: SW -> C4 -> R4 -> BST
        self.SW_NODE += self.buck.SW + self.cbst.p1  # SW pin to bootstrap cap
        self.BST_MID += self.cbst.p2 + self.rbst.p1  # Bootstrap cap to R4
        self.nets.append(self.rbst.p2 + self.buck.BST)  # R4 to BST pin

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
        # self.Ind = Inductor(mpn="WPN4020H6R8MT", manufacturer="Sunlord").insert(self.buck.SW, self.VOUT, short_trace=True)
        self.Ind = Inductor(inductance=L, current_rating=output_current).insert(
            self.buck.SW, self.VOUT, short_trace=True
        )

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
        with CapacitorQuery.refine(
            temperature_coefficient_code="X7R", rated_voltage=output_voltage * 2.0
        ):
            min_output_caps = int(derated_capacitance / out_c) + 1

            # Create output capacitors (C6, C7 = 22uF each)
            if debug:
                print(
                    f"Output Cap: count: {min_output_caps} derated-cap: {derated_capacitance} cap:{out_c}"
                )
            self.output_caps = []
            for _ in range(min_output_caps):
                output_cap = Capacitor(case="0805", capacitance=out_c).insert(
                    self.vout.Vp, self.buck.GND, short_trace=True
                )
                self.output_caps.append(output_cap)

            # Additional 100nF output capacitor (C8) per schematic
            self.c_out_100n = Capacitor(case="0402", capacitance=100.0e-9).insert(
                self.vout.Vp, self.buck.GND, short_trace=True
            )

        # Input capacitance - 10uF per schematic (C1, C2)
        self.input_caps = []
        with CapacitorQuery.refine(
            temperature_coefficient_code="X7R", rated_voltage=input_voltage * 2.0
        ):
            for _ in range(2):
                c_inp_reg = Capacitor(capacitance=10.0e-6).insert(
                    self.buck.VIN, self.buck.GND, short_trace=True
                )
                self.input_caps.append(c_inp_reg)

            # Small input cap
            self.c_inp_sm = Capacitor(capacitance=0.1e-6).insert(
                self.buck.VIN, self.buck.GND, short_trace=True
            )

        # Feedforward cap - 10pF (marked DNP in schematic)
        with CapacitorQuery.refine(case="0402", temperature_coefficient_code="C0G"):
            self.c_ff = Capacitor(capacitance=10.0e-12).insert(
                self.fb_vdiv_ckt.inp, self.fb_vdiv_ckt.out
            )
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
        # 0.5mm clearance for SW_NODE (switch node needs clearance from other nets)
        self.sw_clearance_rule = design_constraint(SwTag(), True).clearance(0.25)

        # 0.5mm clearance for BST_MID (bootstrap node needs clearance from other nets)
        self.bst_clearance_rule = design_constraint(BstTag(), True).clearance(0.25)

        # 1.0mm trace width for VIN and VOUT power nets
        self.power_trace_rule = design_constraint(PowerNetTag()).trace_width(0.25)


Device: type[TPS62933DRLRCircuit] = TPS62933DRLRCircuit
