from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polygon, Polyline, Text
from jitx.feature import Finish, Paste, Silkscreen, Soldermask
from jitxlib.symbols.box import BoxSymbol, Column, Row, PinGroup


class CustomSMDPad1(Pad):
    shape = Polygon(
        [
            (0.100025, 0.249886),
            (0.100025, -0.600051),
            (-0.099975, -0.600051),
            (-0.099975, 0.049911),
        ]
    )
    layer = Soldermask(shape)
    layer = Paste(shape)


class CustomSMDPad2(Pad):
    shape = Polygon(
        [
            (0.250013, 0.100051),
            (-0.599924, 0.100051),
            (-0.599924, -0.099949),
            (0.050038, -0.099949),
        ]
    )
    layer = Soldermask(shape)
    layer = Paste(shape)


class CustomSMDPad3(Pad):
    shape = Polygon(
        [(-0.250013, 0.1), (0.599924, 0.1), (0.599924, -0.1), (-0.050038, -0.1)]
    )
    layer = Soldermask(shape)
    layer = Paste(shape)


class CustomSMDPad4(Pad):
    shape = Polygon(
        [
            (-0.100025, 0.249911),
            (-0.100025, -0.600025),
            (0.099975, -0.600025),
            (0.099975, 0.049936),
        ]
    )
    layer = Soldermask(shape)
    layer = Paste(shape)


class CustomSMDPad5(Pad):
    shape = Polygon(
        [
            (-0.249911, -0.100025),
            (0.600025, -0.100025),
            (0.600025, 0.099975),
            (-0.049936, 0.099975),
        ]
    )
    layer = Soldermask(shape)
    layer = Paste(shape)


class CustomSMDPad6(Pad):
    shape = Polygon(
        [(-0.1, -0.250013), (-0.1, 0.599924), (0.1, 0.599924), (0.1, -0.050038)]
    )
    layer = Soldermask(shape)
    layer = Paste(shape)


class CustomSMDPad7(Pad):
    shape = Polygon(
        [
            (0.100025, -0.249911),
            (0.100025, 0.600025),
            (-0.099975, 0.600025),
            (-0.099975, -0.049936),
        ]
    )
    layer = Soldermask(shape)
    layer = Paste(shape)


class CustomSMDPad8(Pad):
    shape = Polygon(
        [(0.250013, -0.1), (-0.599924, -0.1), (-0.599924, 0.1), (0.050038, 0.1)]
    )
    layer = Soldermask(shape)
    layer = Paste(shape)


class RectSMDPad1(Pad):
    rect = rectangle(2.450013, 2.450013)
    shape = rect
    layer = Soldermask(rect)
    layer = Paste(rect)


class RectSMDPad2(Pad):
    rect = rectangle(0.9, 0.2)
    shape = rect
    layer = Soldermask(rect)
    layer = Paste(rect)


class RectSMDPad3(Pad):
    rect = rectangle(0.2, 0.9)
    shape = rect
    layer = Soldermask(rect)
    layer = Paste(rect)


class C246443(Landpattern):
    p = {
        1: CustomSMDPad1().at(-2.0, -2.385954, on=Side.Top),
        2: RectSMDPad3().at(-1.599949, -2.536068, on=Side.Top),
        3: RectSMDPad3().at(-1.199898, -2.536068, on=Side.Top),
        4: RectSMDPad3().at(-0.800102, -2.536068, on=Side.Top),
        5: RectSMDPad3().at(-0.400051, -2.536068, on=Side.Top),
        6: RectSMDPad3().at(0.0, -2.536068, on=Side.Top),
        7: RectSMDPad3().at(0.400051, -2.536068, on=Side.Top),
        8: RectSMDPad3().at(0.800102, -2.536068, on=Side.Top),
        9: RectSMDPad3().at(1.199898, -2.536068, on=Side.Top),
        10: RectSMDPad3().at(1.599949, -2.536068, on=Side.Top),
        11: CustomSMDPad4().at(2.0, -2.385954, on=Side.Top),
        12: CustomSMDPad3().at(2.386081, -2.000127, on=Side.Top),
        13: RectSMDPad2().at(2.535941, -1.600076, on=Side.Top),
        14: RectSMDPad2().at(2.535941, -1.200025, on=Side.Top),
        15: RectSMDPad2().at(2.535941, -0.799975, on=Side.Top),
        16: RectSMDPad2().at(2.535941, -0.399924, on=Side.Top),
        17: RectSMDPad2().at(2.535941, -0.000127, on=Side.Top),
        18: RectSMDPad2().at(2.535941, 0.399924, on=Side.Top),
        19: RectSMDPad2().at(2.535941, 0.799975, on=Side.Top),
        20: RectSMDPad2().at(2.535941, 1.200025, on=Side.Top),
        21: RectSMDPad2().at(2.535941, 1.600076, on=Side.Top),
        22: CustomSMDPad5().at(2.385827, 1.999873, on=Side.Top),
        23: CustomSMDPad6().at(2.0, 2.385954, on=Side.Top),
        24: RectSMDPad3().at(1.599949, 2.536068, on=Side.Top),
        25: RectSMDPad3().at(1.199898, 2.536068, on=Side.Top),
        26: RectSMDPad3().at(0.800102, 2.536068, on=Side.Top),
        27: RectSMDPad3().at(0.400051, 2.536068, on=Side.Top),
        28: RectSMDPad3().at(0.0, 2.536068, on=Side.Top),
        29: RectSMDPad3().at(-0.400051, 2.536068, on=Side.Top),
        30: RectSMDPad3().at(-0.800102, 2.536068, on=Side.Top),
        31: RectSMDPad3().at(-1.199898, 2.536068, on=Side.Top),
        32: RectSMDPad3().at(-1.599949, 2.536068, on=Side.Top),
        33: CustomSMDPad7().at(-2.0, 2.3857, on=Side.Top),
        34: CustomSMDPad8().at(-2.386081, 1.999873, on=Side.Top),
        35: RectSMDPad2().at(-2.535941, 1.600076, on=Side.Top),
        36: RectSMDPad2().at(-2.535941, 1.200025, on=Side.Top),
        37: RectSMDPad2().at(-2.535941, 0.799975, on=Side.Top),
        38: RectSMDPad2().at(-2.535941, 0.399924, on=Side.Top),
        39: RectSMDPad2().at(-2.535941, -0.000127, on=Side.Top),
        40: RectSMDPad2().at(-2.535941, -0.399924, on=Side.Top),
        41: RectSMDPad2().at(-2.535941, -0.799975, on=Side.Top),
        42: RectSMDPad2().at(-2.535941, -1.200025, on=Side.Top),
        43: RectSMDPad2().at(-2.535941, -1.600076, on=Side.Top),
        44: CustomSMDPad2().at(-2.386081, -2.000127, on=Side.Top),
        45: RectSMDPad1().at(0.0, -0.000127, on=Side.Top),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 4.921006))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -4.921006))
    ref_alt_text = Finish(Text("REF**", 1.0, Anchor.C).at(0.0, -6.921006))

    silk_arcs = [
        Silkscreen(
            ArcPolyline(
                0.059995, [Arc((-2.499873, -2.5), 0.0299719999999999, 0.0, 360.0)]
            )
        ),
        Silkscreen(
            ArcPolyline(0.254001, [Arc((-2.328931, -3.250064), 0.179579, 0.0, 360.0)])
        ),
    ]

    finish_arc = Finish(
        ArcPolyline(0.3, [Arc((-2.020066, -2.859919), 0.150114, 0.0, 360.0)])
    )

    silk_lines = [
        Silkscreen(Polyline(0.254001, [(2.413005, 2.921006), (2.921006, 2.921006)])),
        Silkscreen(Polyline(0.254001, [(2.921006, 2.921006), (2.921006, 2.413005)])),
        Silkscreen(Polyline(0.254001, [(2.921006, -2.413005), (2.921006, -2.921006)])),
        Silkscreen(Polyline(0.254001, [(2.921006, -2.921006), (2.413005, -2.921006)])),
        Silkscreen(
            Polyline(0.254001, [(-2.921006, -2.413005), (-2.921006, -2.540005)])
        ),
        Silkscreen(
            Polyline(0.254001, [(-2.921006, -2.540005), (-2.540005, -2.921006)])
        ),
        Silkscreen(
            Polyline(0.254001, [(-2.540005, -2.921006), (-2.413005, -2.921006)])
        ),
        Silkscreen(Polyline(0.254001, [(-2.921006, 2.413005), (-2.921006, 2.921006)])),
        Silkscreen(Polyline(0.254001, [(-2.921006, 2.921006), (-2.413005, 2.921006)])),
    ]

    # model = Model3D(
    #     "../../3d-models/C246443.wrl",
    #     position=(0, 0, 0),
    #     scale=(1, 1, 1),
    #     rotation=(0, 0, -90)
    # )


class IS31FL3236A_QFLS2_TR(Component):
    """IS31FL3236A is comprised of 36 constant current channels each with independent PWM control, designed for driving LEDs"""

    mpn = "IS31FL3236A-QFLS2-TR"
    reference_designator_prefix = "U"

    # Control pins
    VCC = Port()
    SCL = Port()
    SDA = Port()
    SDB = Port()
    AD = Port()
    R_EXT = Port()
    EPAD = Port()

    # Ground pins
    GND = [Port() for _ in range(0, 2)]

    # Output pins (36 channels)
    OUT = {i: Port() for i in range(1, 37)}

    landpattern = C246443()
    symbol = BoxSymbol(
        rows=[
            Row(left=[PinGroup([VCC, SCL, SDA, SDB, AD, R_EXT])]),
            Row(right=[PinGroup(tuple(OUT.values()))]),
        ],
        columns=[Column(down=[PinGroup([EPAD, GND[0], GND[1]])])],
    )

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                VCC: [landpattern.p[38]],
                SCL: [landpattern.p[42]],
                SDA: [landpattern.p[41]],
                SDB: [landpattern.p[36]],
                AD: [landpattern.p[37]],
                R_EXT: [landpattern.p[40]],
                EPAD: [landpattern.p[45]],
                GND[0]: [landpattern.p[17]],
                GND[1]: [landpattern.p[39]],
                OUT[1]: [landpattern.p[43]],
                OUT[2]: [landpattern.p[44]],
                OUT[3]: [landpattern.p[1]],
                OUT[4]: [landpattern.p[2]],
                OUT[5]: [landpattern.p[3]],
                OUT[6]: [landpattern.p[4]],
                OUT[7]: [landpattern.p[5]],
                OUT[8]: [landpattern.p[6]],
                OUT[9]: [landpattern.p[7]],
                OUT[10]: [landpattern.p[8]],
                OUT[11]: [landpattern.p[9]],
                OUT[12]: [landpattern.p[10]],
                OUT[13]: [landpattern.p[11]],
                OUT[14]: [landpattern.p[12]],
                OUT[15]: [landpattern.p[13]],
                OUT[16]: [landpattern.p[14]],
                OUT[17]: [landpattern.p[15]],
                OUT[18]: [landpattern.p[16]],
                OUT[19]: [landpattern.p[18]],
                OUT[20]: [landpattern.p[19]],
                OUT[21]: [landpattern.p[20]],
                OUT[22]: [landpattern.p[21]],
                OUT[23]: [landpattern.p[22]],
                OUT[24]: [landpattern.p[23]],
                OUT[25]: [landpattern.p[24]],
                OUT[26]: [landpattern.p[25]],
                OUT[27]: [landpattern.p[26]],
                OUT[28]: [landpattern.p[27]],
                OUT[29]: [landpattern.p[28]],
                OUT[30]: [landpattern.p[29]],
                OUT[31]: [landpattern.p[30]],
                OUT[32]: [landpattern.p[31]],
                OUT[33]: [landpattern.p[32]],
                OUT[34]: [landpattern.p[33]],
                OUT[35]: [landpattern.p[34]],
                OUT[36]: [landpattern.p[35]],
            }
        ),
    ]

    # Properties
    lcsc = "C246443"
    # VCC.power_pin = {"voltage_range": (2.7, 5.5)}  # V

    # Property for datasheet URL
    datasheet = "https://datasheet.lcsc.com/lcsc/1810010543_ISSI-Integrated-Silicon-Solution-IS31FL3236A-QFLS2-TR_C246443.pdf"


Device: type[IS31FL3236A_QFLS2_TR] = IS31FL3236A_QFLS2_TR
