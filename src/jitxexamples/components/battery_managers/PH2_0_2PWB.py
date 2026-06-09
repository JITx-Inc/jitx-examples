from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.common import Power
from jitx.component import Component as JITXComponent
from jitx.circuit import Circuit
from jitx.landpattern import Landpattern, Pad
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polyline, Text
from jitx.feature import Custom, Paste, Silkscreen, Soldermask, Courtyard
from jitxlib.symbols.box import BoxSymbol, Row, PinGroup


class RectangleSmdPad(Pad):
    shape = rectangle(0.9, 1.7)
    solder_mask = [Soldermask(rectangle(1.000, 1.800))]
    paste = [Paste(rectangle(1.000, 1.800))]


class RectangleSmdPad1(Pad):
    shape = rectangle(0.8, 3)
    solder_mask = [Soldermask(rectangle(0.900, 3.000))]
    paste = [Paste(rectangle(0.900, 3.000))]


class LandpatternPH2_0_2PWB(Landpattern):
    name = "CONN-SMD_2P-P2.00_PH2.0-SPWB"
    p = {
        1: RectangleSmdPad().at((1.000, -3.5)),
        2: RectangleSmdPad().at((-1.000, -3.5)),
        3: RectangleSmdPad1().at((-3.250, 2.85)),
        4: RectangleSmdPad1().at((3.250, 2.85)),
    }
    pcb_layer_reference = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 6.1066)))
    pcb_layer_value = Custom(
        Text(">VALUE", 0.5, Anchor.W).at((-0.75, 5.1066)), name="Fab"
    )
    custom_layer = [
        Custom(Polyline(0.254, [(-3.200, -1.85), (-3.200, -3.45)]), name="Fab"),
        Custom(Polyline(0.254, [(3.200, -3.45), (3.200, -1.85)]), name="Fab"),
        Custom(Polyline(0.254, [(3.200, -1.85), (-3.200, -1.85)]), name="Fab"),
        Custom(Polyline(0.254, [(-4.000, 4.15), (4.000, 4.15)]), name="Fab"),
        Custom(Polyline(0.254, [(4.000, 4.15), (4.000, -3.45)]), name="Fab"),
        Custom(Polyline(0.254, [(-4.000, -3.45), (-4.000, 4.15)]), name="Fab"),
        Custom(Polyline(0.254, [(-3.200, -3.45), (-4.000, -3.45)]), name="Fab"),
        Custom(Polyline(0.254, [(4.000, -3.45), (3.200, -3.45)]), name="Fab"),
        Custom(ArcPolyline(0.06, [Arc((4.000, -3.925), 0.03, 0, -360)]), name="Fab"),
    ]
    silkscreen = [
        Silkscreen(Polyline(0.254, [(-3.200, -1.85), (-3.200, -3.45)])),
        Silkscreen(Polyline(0.254, [(3.200, -3.45), (3.200, -1.85)])),
        Silkscreen(Polyline(0.254, [(3.200, -1.85), (-3.200, -1.85)])),
        Silkscreen(Polyline(0.254, [(4.000, 4.15), (4.000, -3.45)])),
        Silkscreen(Polyline(0.254, [(-2.500, 4.15), (2.500, 4.15)])),
        Silkscreen(Polyline(0.254, [(-4.000, -3.45), (-4.000, 4.15)])),
        Silkscreen(Polyline(0.254, [(-3.200, -3.45), (-4.000, -3.45)])),
        Silkscreen(Polyline(0.254, [(4.000, -3.45), (3.200, -3.45)])),
    ]
    courtyard = [Courtyard(rectangle(8.255, 8.802))]


class Component(JITXComponent):
    description = "Battery connector module for 2.0mm pitch battery connection"
    manufacturer = "BOOMELE"
    mpn = "C47647"
    reference_designator_prefix = "J"
    datasheet = "https://datasheet.lcsc.com/lcsc/1912111436_BOOMELE-Boom-Precision-Elec-C47647_C47647.pdf"

    pin1 = Port()
    pin2 = Port()
    pin3 = Port()
    pin4 = Port()

    landpattern = LandpatternPH2_0_2PWB()

    symbol = BoxSymbol(
        rows=[
            Row(
                left=[PinGroup([pin1, pin2, pin3, pin4])],
            ),
        ],
    )

    cmappings = [
        PadMapping(
            {
                pin1: landpattern.p[1],
                pin2: landpattern.p[2],
                pin3: landpattern.p[3],
                pin4: landpattern.p[4],
            }
        ),
    ]


class PH2_0_2PWB(Circuit):
    """
    PH2-0-2PWB Module
    Battery connector module for 2.0mm pitch battery connection
    """

    battery = Power()
    mounting = Port()

    # Battery connector from LCSC database
    connector = Component()

    # Circuit connections
    nets = [
        # Battery connector connections
        battery.Vn + connector.pin1,  # Ground to battery pin 1
        battery.Vp + connector.pin2,  # Power to battery pin 2
        mounting + connector.pin3 + connector.pin4,
    ]


Device: type[PH2_0_2PWB] = PH2_0_2PWB
