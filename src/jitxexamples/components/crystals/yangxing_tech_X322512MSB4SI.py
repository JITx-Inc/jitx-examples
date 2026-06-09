"""
Yangxing Tech 12Mhz Crystal resonator
=====================================

Component definition for YXC Crystal resonator
12 MHz, 20 pF, 20ppm, -20~+70C
"""

from jitx.anchor import Anchor
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polygon, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.component import Component


class RectangleSmdPad(Pad):
    shape = rectangle(1.4, 1.2)
    solder_mask = [Soldermask(rectangle(1.502, 1.302))]
    paste = [Paste(rectangle(1.502, 1.302))]


class LandpatternOSC_SMD_4P_L3_2_W2_5_BL(Landpattern):
    name = "OSC-SMD_4P-L3.2-W2.5-BL"
    p = {
        1: RectangleSmdPad().at((-0.973, -0.748)),
        2: RectangleSmdPad().at((1.227, -0.748)),
        3: RectangleSmdPad().at((1.227, 1.002)),
        4: RectangleSmdPad().at((-0.973, 1.002)),
    }
    reference_designator = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 3.5596)))
    value_label = Custom(Text(">VALUE", 0.5, Anchor.W).at((-0.75, 2.5596)), name="Fab")
    silkscreen = [
        Silkscreen(
            Polyline(0.152, [(-2.159, -1.27), (-2.159, -1.778), (-1.651, -1.778)])
        ),
        Silkscreen(
            Polyline(
                0.152,
                [
                    (-1.902, -1.551),
                    (-1.902, 1.778),
                    (2.159, 1.778),
                    (2.159, 0.127),
                    (2.159, -1.524),
                    (2.159, -1.524),
                    (-1.902, -1.551),
                ],
            )
        ),
    ]
    custom_layer = [
        Custom(ArcPolyline(0.06, [Arc((-1.473, -1.123), 0.03, 0, -360)]), name="Fab"),
        Custom(ArcPolyline(0.254, [Arc((-0.961, -1.44), 0.127, 0, -360)]), name="Fab"),
        Custom(
            Polygon(
                [
                    (-1.359, -0.301),
                    (-1.323, -0.301),
                    (-1.323, -0.877),
                    (-1.359, -0.877),
                    (-1.359, -0.301),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (-1.395, -0.301),
                    (-1.359, -0.301),
                    (-1.359, -0.877),
                    (-1.395, -0.877),
                    (-1.395, -0.301),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (-1.431, -0.301),
                    (-1.395, -0.301),
                    (-1.395, -0.877),
                    (-1.431, -0.877),
                    (-1.431, -0.301),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (-1.467, -0.337),
                    (-1.431, -0.337),
                    (-1.431, -0.877),
                    (-1.467, -0.877),
                    (-1.467, -0.337),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (-1.503, -0.337),
                    (-1.467, -0.337),
                    (-1.467, -0.445),
                    (-1.503, -0.445),
                    (-1.503, -0.337),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (-1.539, -0.373),
                    (-1.503, -0.373),
                    (-1.503, -0.481),
                    (-1.539, -0.481),
                    (-1.539, -0.373),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (-1.575, -0.409),
                    (-1.539, -0.409),
                    (-1.539, -0.481),
                    (-1.575, -0.481),
                    (-1.575, -0.409),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (-1.611, -0.409),
                    (-1.575, -0.409),
                    (-1.575, -0.481),
                    (-1.611, -0.481),
                    (-1.611, -0.409),
                ]
            ),
            name="Fab",
        ),
    ]
    courtyard = Courtyard(rectangle(4.47, 3.708))
    model3ds = Model3D(
        "yangxing_tech_X322512MSB4SI.stp",
        position=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
        rotation=(0.0, 0.0, 0.0),
    )


class SymbolX322512MSB4SI(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    OSC2 = Pin((4, 2), 2, Direction.Right)
    OSC1 = Pin((-4, -2), 2, Direction.Left)
    GND0 = Pin((4, -2), 2, Direction.Right)
    GND1 = Pin((-4, 2), 2, Direction.Left)
    reference = Text(">REF", 0.55559, Anchor.C).at((0, 3.57481))
    value = Text(">VALUE", 0.55559, Anchor.C).at((0, 2.78741))
    shapes = [
        rectangle(8, 8),
        Polyline(
            0.254, [(0.6, 1.4), (0.6, -1.4), (-0.6, -1.4), (-0.6, 1.4), (0.6, 1.4)]
        ),
        Polyline(0.254, [(-1, -1.4), (-1, 1.4)]),
        Polyline(0.254, [(1, -1.4), (1, 1.4)]),
        Polyline(0.254, [(-4, -2), (-2, -2), (-2, 0), (-1.2, 0)]),
        Polyline(0.254, [(4, 2), (2, 2), (2, 0), (1.2, 0)]),
        Polyline(0.254, [(-0.6, -1.4), (-0.6, 1.4), (0.6, 1.4), (0.6, -1.4)]),
        Polyline(0.254, [(1, -0.8), (1, 0.8)]),
        Polyline(0.254, [(0.6, -1.4), (-0.6, -1.4)]),
        Polyline(0.254, [(-1, -0.8), (-1, 0.8)]),
    ]


class X322512MSB4SI(Component):
    """12 Mhz, 20pf, 20ppm Crystal Resonator"""

    manufacturer = "Yangxing Tech"
    mpn = "X322512MSB4SI"
    reference_designator_prefix = "X"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2403291504_YXC-Crystal-Oscillators-X322512MSB4SI_C9002.pdf"

    OSC2 = Port()
    """Oscillator Pin 2"""
    OSC1 = Port()
    """Oscillator Pin 1"""
    GND0 = Port()
    """GND Pin 1"""
    GND1 = Port()
    """GND Pin 2"""

    landpattern = LandpatternOSC_SMD_4P_L3_2_W2_5_BL()
    symbol = SymbolX322512MSB4SI()
    cmappings = [
        SymbolMapping(
            {OSC2: symbol.OSC2, OSC1: symbol.OSC1, GND0: symbol.GND0, GND1: symbol.GND1}
        ),
        PadMapping(
            {
                OSC2: landpattern.p[3],
                OSC1: landpattern.p[1],
                GND0: landpattern.p[2],
                GND1: landpattern.p[4],
            }
        ),
    ]


Device: type[X322512MSB4SI] = X322512MSB4SI
