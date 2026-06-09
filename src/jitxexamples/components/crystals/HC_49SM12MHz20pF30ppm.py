from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polyline, Text
from jitx.feature import Finish, Paste, Silkscreen, Soldermask
from jitx.symbol import Direction, Pin, Symbol


class RectSMDPad(Pad):
    rect = rectangle(5.5, 1.3)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class C111117(Landpattern):
    p = {
        1: RectSMDPad().at(-4.552959, 0.0, rotate=180, on=Side.Top),
        2: RectSMDPad().at(4.552959, 0.0, rotate=180, on=Side.Top),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 4.413005))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -4.413005))
    ref_alt_text = Finish(Text("REF**", 1.0, Anchor.C).at(0.0, -6.413005))

    silk_lines = [
        Silkscreen(Polyline(0.1524, [(-5.715011, 2.413005), (-5.7, 0.662408)])),
        Silkscreen(Polyline(0.1524, [(-5.7, -0.662408), (-5.715011, -2.413005)])),
        Silkscreen(Polyline(0.1524, [(-5.715011, -2.413005), (5.715011, -2.413005)])),
        Silkscreen(Polyline(0.1524, [(5.715011, -2.413005), (5.7, -0.662408)])),
        Silkscreen(Polyline(0.1524, [(5.7, 0.662408), (5.715011, 2.413005)])),
        Silkscreen(Polyline(0.1524, [(-5.715011, -2.413005), (5.715011, -2.413005)])),
        Silkscreen(Polyline(0.1524, [(5.7, 0.662408), (5.715011, 2.413005)])),
        Silkscreen(Polyline(0.1524, [(5.715011, 2.413005), (-5.715011, 2.413005)])),
        Silkscreen(Polyline(0.1524, [(5.715011, 2.413005), (-5.715011, 2.413005)])),
        Silkscreen(Polyline(0.1524, [(5.715011, -2.413005), (5.7, -0.662408)])),
        Silkscreen(Polyline(0.1524, [(-5.715011, 2.413005), (-5.7, 0.662408)])),
        Silkscreen(Polyline(0.1524, [(-5.7, -0.662408), (-5.715011, -2.413005)])),
    ]

    silk_arcs = [
        Silkscreen(
            ArcPolyline(
                0.059995, [Arc((-6.340107, -2.400051), 0.0299719999999999, 0.0, 360.0)]
            )
        ),
    ]

    # model = Model3D(
    #     "../../3d-models/C111117.wrl",
    #     position=(0, 0, 0),
    #     scale=(1, 1, 1),
    #     rotation=(0, 0, 0)
    # )


class HC_49SM12MHz20pF30ppm_Symbol(Symbol):
    pin_name_size = 0.6
    pad_name_size = 0.6

    p1 = Pin(at=(-1, 0), direction=Direction.Left, length=1)  # Pin 1
    p2 = Pin(at=(1, 0), direction=Direction.Right, length=1)  # Pin 2

    ref_text = Text(">REF", 1.27, Anchor.C).at(0.0, 2.54)
    value_text = Text(">VALUE", 1.27, Anchor.C).at(0.0, -5.08)

    # Crystal symbol elements
    crystal_lines = [
        Polyline(0.20, [(0.2, 1.2), (-0.2, 1.2)]),
        Polyline(0.20, [(0.8, 0.0), (1, 0.0)]),
        Polyline(0.20, [(0.2, -1.2), (0.2, 1.2)]),
        Polyline(0.20, [(-0.2, 1.2), (-0.2, -1.2)]),
        Polyline(0.20, [(-0.2, -1.2), (0.2, -1.2)]),
        Polyline(0.20, [(-0.8, 1.4), (-0.8, -1.4)]),
        Polyline(0.20, [(-1, 0.0), (-0.8, 0.0)]),
        Polyline(0.20, [(0.8, 1.4), (0.8, -1.4)]),
    ]


class HC_49SM12MHz20pF30ppm(Component):
    description = "Crystal Oscillator 20pF HC-49S-SMD"
    mpn = "HC-49SM12MHz20pF30ppm"
    reference_designator_prefix = "Y"

    p1 = Port()  # Pin 1
    p2 = Port()  # Pin 2

    landpattern = C111117()
    symbol = HC_49SM12MHz20pF30ppm_Symbol()

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                p1: [landpattern.p[1]],  # Pin 1 to pad 1
                p2: [landpattern.p[2]],  # Pin 2 to pad 2
            }
        ),
    ]

    # Crystal resonator properties
    crystal_resonator = {
        "load_capacitance": 20.0e-12,  # 20pF
        "shunt_capacitance": 7.0e-12,  # 7pF
        "motional_capacitance": 5.0e-15,  # 5fF
        "motional_inductance": 50.0,  # 50H
        "frequency": 12.0e6,  # 12MHz
        "frequency_tolerance": 20.0e-6,  # 20ppm
        "frequency_stability": 100.0e-6,  # 100ppm
    }

    # Property for datasheet URL
    datasheet = "https://datasheet.lcsc.com/lcsc/1810170913_TAE-Zhejiang-Abel-Elec-TAXM12M2GLFBET2T_C111117.pdf"


Device: type[HC_49SM12MHz20pF30ppm] = HC_49SM12MHz20pF30ppm
