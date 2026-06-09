from jitx.anchor import Anchor
from jitx.component import Component
from jitx.container import inline
from jitx.feature import Courtyard, Custom, Silkscreen, Soldermask, Paste
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polygon, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping


class RectangleSMDPad(Pad):
    shape = rectangle(0.4, 0.7)
    soldermask = Soldermask(rectangle(0.502, 0.802))
    paste = Paste(rectangle(0.502, 0.802))


class NTA4151PT1G(Component):
    """
    NTA4151PT1G P-Channel MOSFET

    20V 760mA 360mΩ@4.5V,350mA 301mW P Channel MOSFET
    Manufacturer: ON Semiconductor
    """

    name = "C54876"
    manufacturer = "ON Semiconductor"
    mpn = "NTA4151PT1G"
    datasheet = (
        "https://datasheet.lcsc.com/lcsc/1809212222_onsemi-NTA4151PT1G_C54876.pdf"
    )
    reference_designator_prefix = "Q"

    # MOSFET pins
    D = Port()  # Drain
    G = Port()  # Gate
    S = Port()  # Source

    @inline
    class landpattern(Landpattern):
        # Pads
        p = {
            1: RectangleSMDPad().at(0.6, -0.509, rotate=90),
            2: RectangleSMDPad().at(0.6, 0.507, rotate=90),
            3: RectangleSMDPad().at(-0.6, 0, rotate=90),
        }

        # Labels
        labels = [
            Silkscreen(Text(">REF", 0.5, Anchor.W).at(-0.75, 2.683)),
            Custom(Text(">VALUE", 0.5, Anchor.W).at(-0.75, 1.683), name="Fab"),
        ]

        # Silkscreen
        silkscreen = [
            Silkscreen(Polyline(0.254, [(-0.4, 0.85), (-0.4, 0.427)])),
            Silkscreen(Polyline(0.254, [(-0.4, -0.428), (-0.4, -0.85)])),
            Silkscreen(Polyline(0.254, [(-0.4, 0.85), (0.068, 0.85)])),
            Silkscreen(Polyline(0.254, [(-0.4, -0.85), (0.068, -0.85)])),
            Silkscreen(Polyline(0.254, [(0.4, 0.076), (0.4, -0.077)])),
        ]

        # Fab drawing
        fab_drawing = [
            Custom(ArcPolyline(0.06, [Arc((0.8, -0.801), 0.03, 0, -360)]), name="Fab"),
            Custom(ArcPolyline(0.1, [Arc((1.025, -0.5), 0.05, 0, -360)]), name="Fab"),
        ]

        # Courtyard
        courtyard = Courtyard(rectangle(1.702, 1.954))

    @inline
    class symbol(Symbol):
        pin_name_size = 0.7
        pad_name_size = 0.7

        # Pin definitions
        D = Pin((2, 4), 2, Direction.Up)
        G = Pin((-4, -2), 2, Direction.Left)
        S = Pin((2, -2), 2, Direction.Down)

        # Text elements
        value = Text(">VALUE", 0.7056, Anchor.C).at(0, 4.89)
        reference = Text(">REF", 0.7056, Anchor.C).at(0, 5.67)

        # Symbol artwork - MOSFET symbol
        art = [
            # Connection circles
            Circle(radius=0.1).at(-4, -2),
            Circle(radius=0.1).at(2, -2),
            Circle(radius=0.1).at(2, 0),
            Circle(radius=0.1).at(2, 4),
            Circle(radius=0.1).at(2, 0.6),
            # Drain connections
            Polyline(0.2, [(2, 0), (4, 0), (4, 1.6)]),
            Polyline(0.2, [(2, 3.4), (2, 4), (4, 4), (4, 2.6)]),
            # Channel structure
            Polyline(0.2, [(2, 3.4), (0, 3.4)]),
            Polyline(0.2, [(0, 2), (2, 2), (2, 0)]),
            Polyline(0.2, [(2, 0.6), (0, 0.6)]),
            # Gate structure
            Polyline(0.2, [(-0.4, 3.8), (-0.4, 0.2)]),
            Polyline(0.2, [(0, 3), (0, 3.8)]),
            Polyline(0.2, [(0, 1.6), (0, 2.4)]),
            Polyline(0.2, [(0, 0.2), (0, 1)]),
            # Gate connection
            Polyline(0.2, [(-2, 2), (-0.4, 2)]),
            # Body diode
            Polyline(0.2, [(-0.8, -2.6), (-0.8, -1.4), (0, -2), (-0.8, -2.6)]),
            Polyline(0.2, [(-2.2, -2.8), (-2.2, -1.2)]),
            Polyline(0.2, [(-2.2, -2), (-1.4, -2.6), (-1.4, -1.4), (-2.2, -2)]),
            # Source connection
            Polyline(0.2, [(2, -2), (-4, -2)]),
            Polyline(0.2, [(2, -2), (2, 0)]),
            # Gate resistor symbol
            Polyline(
                0.2,
                [
                    (-2, 2),
                    (-2.2, 2.4),
                    (-2.4, 1.6),
                    (-2.8, 2.4),
                    (-3, 1.6),
                    (-3.4, 2.4),
                    (-3.6, 1.6),
                    (-3.8, 2),
                    (-4, 2),
                    (-4, -2),
                ],
            ),
            # Additional symbol details
            Polyline(0.2, [(-1.8, -3.2), (-2.2, -2.8)]),
            Polyline(0.2, [(-2.2, -1.2), (-2.6, -0.8)]),
            Polyline(0.2, [(0, -2.8), (0, -1.2)]),
            Polyline(0.2, [(0.4, -3.2), (0, -2.8)]),
            Polyline(0.2, [(0, -1.2), (-0.4, -0.8)]),
            # Arrows/triangles
            Polygon([(2, 2), (0.8, 2.4), (0.8, 1.6)]),
            Polygon([(4, 1.6), (4.6, 2.6), (3.4, 2.6)]),
        ]

    # Pin mapping
    padmapping = PadMapping(
        {
            G: landpattern.p[1],  # Gate
            S: landpattern.p[2],  # Source
            D: landpattern.p[3],  # Drain
        }
    )

    # Symbol mapping
    symbolmapping = SymbolMapping(
        {
            D: symbol.D,
            G: symbol.G,
            S: symbol.S,
        }
    )


Device: type[NTA4151PT1G] = NTA4151PT1G
