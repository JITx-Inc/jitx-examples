from dataclasses import dataclass
import math
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.container import inline
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Port
from jitx.property import Property
from jitx.shapes import Shape
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polygon, Polyline, Text
from jitx.symbol import Pin, Symbol, SymbolMapping, Direction
from jitx.transform import Point
from jitxlib.symbols.common import DEF_LINE_WIDTH


class RGBLed(Port):
    r = Port()
    g = Port()
    b = Port()
    a = Port()


class RectangleSMDPad(Pad):
    shape = rectangle(0.7, 0.8)
    soldermask = Soldermask(rectangle(0.802, 0.902))
    paste = Paste(rectangle(0.802, 0.902))


def _draw_opto(x: float, y: float) -> list[Shape[Circle] | Polyline]:
    """
    Draw an optoelectronic symbol (LED/photo diode) at the given coordinates.

    Args:
        x: X coordinate for the center of the symbol
        y: Y coordinate for the center of the symbol

    Returns:
        List of shapes representing the optoelectronic symbol
    """
    return [
        Circle(radius=1.5).at(x, y),
        Polyline(DEF_LINE_WIDTH, [(x + 1, y + 0.2), (x + 1.8, (y - 0.6))]),
        Polyline(DEF_LINE_WIDTH, [(x + 1, (y - 0.4)), (x + 1.8, (y - 1.2))]),
        Polyline(
            DEF_LINE_WIDTH,
            [(x + 1.5, (y - 0.6)), (x + 1.8, (y - 0.6)), (x + 1.8, (y - 0.3))],
        ),
        Polyline(
            DEF_LINE_WIDTH,
            [(x + 1.5, (y - 1.2)), (x + 1.8, (y - 1.2)), (x + 1.8, (y - 0.9))],
        ),
    ]


def _draw_triangle(p0: Point, p1: Point, w: float) -> Polygon:
    """
    Draw a triangle between two points with specified width.

    Args:
        p0: First point of the triangle base
        p1: Second point of the triangle base
        w: Width of the triangle

    Returns:
        Polygon representing the triangle
    """
    x0, y0 = p0
    x1, y1 = p1
    dx = x1 - x0
    dy = y1 - y0
    length = math.sqrt(dx * dx + dy * dy)
    ux = dx / length
    uy = dy / length
    w2 = w / 2
    return Polygon(
        [
            p1,
            (x0 - (w2 * uy), y0 + (w2 * ux)),
            (x0 + (w2 * uy), y0 - (w2 * ux)),
        ]
    )


@dataclass
class LEDProperty(Property):
    """Property class for LED components with forward voltage and current specifications."""

    forward_voltage: float
    mcd_current: tuple[tuple[float, float], ...]


class FM_B2020RGBA_HG(Component):
    """
    FM-B2020RGBA-HG RGB LED Component

    RGB SMD,2.1x2.1mm Light Emitting Diodes (LED) ROHS
    Manufacturer: Foshan NationStar Optoelectronics
    """

    manufacturer = "Foshan NationStar Optoelectronics"
    mpn = "FM-B2020RGBA-HG"
    datasheet = "https://datasheet.lcsc.com/lcsc/1810231210_Foshan-NationStar-Optoelectronics-FM-B2020RGBA-HG_C108793.pdf"
    reference_designator_prefix = "D"

    # Ports
    led = RGBLed()

    @inline
    class landpattern(Landpattern):
        # Pads
        p = {
            1: RectangleSMDPad().at(-0.85, 0.55, rotate=270),
            2: RectangleSMDPad().at(0.85, 0.55, rotate=270),
            3: RectangleSMDPad().at(0.85, -0.55, rotate=270),
            4: RectangleSMDPad().at(-0.85, -0.55, rotate=270),
        }

        # Labels
        labels = [
            Silkscreen(Text(">REF", 0.5, Anchor.W).at(-0.75, 2.908)),
            Custom(Text(">VALUE", 0.5, Anchor.W).at(-0.75, 1.908), name="Fab"),
        ]

        # Silkscreen
        silkscreen = [
            Silkscreen(
                Polyline(
                    0.152,
                    [
                        (-1.126, 0.971),
                        (-1.126, 1.127),
                        (-1.126, 1.127),
                        (1.126, 1.127),
                        (1.126, 1.127),
                        (1.126, 0.971),
                    ],
                )
            ),
            Silkscreen(
                Polyline(
                    0.152,
                    [
                        (-1.126, -0.97),
                        (-1.126, -1.126),
                        (-1.126, -1.126),
                        (1.126, -1.126),
                        (1.126, -1.126),
                        (1.126, -0.97),
                    ],
                )
            ),
            Silkscreen(ArcPolyline(0.25, [Arc((-1.62, 0.73), 0.125, 0, -360)])),
        ]

        # Fab drawing - simplified version of the complex polygons
        fab_drawing = [
            Custom(ArcPolyline(0.06, [Arc((-1.05, 1.051), 0.03, 0, -360)]), name="Fab"),
            # Note: The original has hundreds of small polygon elements
            # For brevity, including key structural elements only
            Custom(
                Polygon(
                    [
                        (-0.8, 1.15),
                        (-1.22, 1.15),
                        (-1.22, 0.76),
                        (-0.8, 1.15),
                    ]
                ),
                name="Fab",
            ),
            Custom(
                Polygon(
                    [
                        (0.59, -0.48),
                        (1.14, -0.48),
                        (1.14, -0.63),
                        (0.59, -0.63),
                        (0.59, -0.62),
                        (0.59, -0.48),
                    ]
                ),
                name="Fab",
            ),
            Custom(
                Polygon(
                    [
                        (0.79, -0.81),
                        (0.79, -0.26),
                        (0.94, -0.26),
                        (0.94, -0.81),
                        (0.93, -0.81),
                        (0.79, -0.81),
                    ]
                ),
                name="Fab",
            ),
        ]

        # Courtyard
        courtyard = Courtyard(rectangle(2.502, 2.405))

    @inline
    class RGBDiodeSymbol(Symbol):
        # Pin positions
        xr = -4  # Red channel X position
        xg = 0  # Green channel X position
        xb = 4  # Blue channel X position
        ybot = 0.8  # Bottom Y position for common connections

        # Pin definitions
        a = Pin((0, 4), direction=Direction.Up)  # Anode (common positive)
        r = Pin((xr, -3), direction=Direction.Down)  # Red channel
        g = Pin((xg, -3), direction=Direction.Down)  # Green channel
        b = Pin((xb, -3), direction=Direction.Down)  # Blue channel

        # Symbol artwork
        optos = []
        art = []

        # Red channel
        optos.append(_draw_opto(xr, 0))
        art.extend(
            [
                _draw_triangle((xr, ybot), (xr, (ybot - 1.6)), 2),
                Polyline(DEF_LINE_WIDTH, [(xr, (ybot - 1.6)), (xr, -3)]),
                Polyline(
                    DEF_LINE_WIDTH, [(xr - 1, (ybot - 1.6)), (xr + 1, (ybot - 1.6))]
                ),
                Text("R", 1, Anchor.C).at(xr - 0.6, -2.4),
            ]
        )

        # Green channel
        optos.append(_draw_opto(xg, 0))
        art.extend(
            [
                _draw_triangle((xg, ybot), (xg, (ybot - 1.6)), 2),
                Polyline(DEF_LINE_WIDTH, [(xg, (ybot - 1.6)), (xg, -3)]),
                Polyline(
                    DEF_LINE_WIDTH, [(xg - 1, (ybot - 1.6)), (xg + 1, (ybot - 1.6))]
                ),
                Text("G", 1, Anchor.C).at(xg - 0.6, -2.4),
            ]
        )

        # Blue channel
        optos.append(_draw_opto(xb, 0))
        art.extend(
            [
                _draw_triangle((xb, ybot), (xb, (ybot - 1.6)), 2),
                Polyline(DEF_LINE_WIDTH, [(xb, (ybot - 1.6)), (xb, -3)]),
                Polyline(
                    DEF_LINE_WIDTH, [(xb - 1, (ybot - 1.6)), (xb + 1, (ybot - 1.6))]
                ),
                Text("B", 1, Anchor.C).at(xb - 0.6, -2.4),
            ]
        )

        # Common connections
        art.extend(
            [
                Polyline(DEF_LINE_WIDTH, [(xr, ybot), (xr, ybot + 1)]),
                Polyline(DEF_LINE_WIDTH, [(xg, ybot), (xg, 4)]),
                Polyline(DEF_LINE_WIDTH, [(xb, ybot), (xb, ybot + 1)]),
                Polyline(DEF_LINE_WIDTH, [(xr, ybot + 1), (xb, ybot + 1)]),
            ]
        )

        # Reference and value labels
        ref = Text(">REF", 0.5, Anchor.W).at(1, 3.7)
        val = Text(">VALUE", 0.5, Anchor.W).at(1, 3)

    # Pin mapping
    padmapping = PadMapping(
        {
            led.a: landpattern.p[3],  # Anode
            led.r: landpattern.p[1],  # Red cathode
            led.b: landpattern.p[2],  # Blue cathode
            led.g: landpattern.p[4],  # Green cathode
        }
    )

    symbolmapping = SymbolMapping(
        {
            led.a: RGBDiodeSymbol.a,
            led.r: RGBDiodeSymbol.r,
            led.b: RGBDiodeSymbol.b,
            led.g: RGBDiodeSymbol.g,
        }
    )

    def __init__(self):
        LEDProperty(2, ((0, 0), (68.75, 10e-3))).assign(self.led.r)
        LEDProperty(3, ((0, 0), (300, 10e-3))).assign(self.led.g)
        LEDProperty(3, ((0, 0), (83, 10e-3))).assign(self.led.b)


Device: type[FM_B2020RGBA_HG] = FM_B2020RGBA_HG
