"""
Littelfuse SMBJ43CA TVS Diode

Component definition for Littelfuse SMBJ43CA 43V bidirectional TVS diode
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
    shape = rectangle(2.047, 2.241)
    solder_mask = [Soldermask(rectangle(2.149, 2.343))]
    paste = [Paste(rectangle(2.149, 2.343))]


class LandpatternSMB_L4_4_W3_6_LS5_4_BI(Landpattern):
    name = "SMB_L4.4-W3.6-LS5.4-BI"
    p = {
        1: RectangleSmdPad().at((-2.54, 0)),
        2: RectangleSmdPad().at((2.54, 0)),
    }
    reference_designator = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 3.6866)))
    value_label = Custom(Text(">VALUE", 0.5, Anchor.W).at((-0.75, 2.6866)), name="Fab")
    silkscreen = [
        Silkscreen(Polyline(0.152, [(2.667, -1.905), (-2.599, -1.89)])),
        Silkscreen(Polyline(0.152, [(2.663, 1.905), (-2.591, 1.888)])),
        Silkscreen(Polyline(0.254, [(-1.331, -0.007), (1.364, -0.007)])),
        Silkscreen(
            Polyline(
                0.254,
                [
                    (0.889, -1.016),
                    (0.889, 1.016),
                    (0.889, 0.889),
                    (0, 0),
                    (0.889, -0.889),
                    (0.889, -1.016),
                ],
            )
        ),
        Silkscreen(
            Polyline(
                0.254,
                [
                    (-0.889, 1.016),
                    (-0.889, -1.016),
                    (-0.889, -0.889),
                    (0, 0),
                    (-0.889, 0.889),
                    (-0.889, 1.016),
                ],
            )
        ),
        Silkscreen(Polyline(0.152, [(-1.331, -1.886), (-1.331, 1.887)])),
        Silkscreen(Polyline(0.152, [(1.364, -1.886), (1.364, 1.887)])),
        Silkscreen(
            Polygon(
                [
                    (2.286, -1.905),
                    (2.286, -1.215),
                    (2.743, -1.215),
                    (2.743, -1.905),
                    (2.286, -1.905),
                ]
            )
        ),
        Silkscreen(
            Polygon(
                [
                    (2.286, 1.905),
                    (2.286, 1.216),
                    (2.743, 1.216),
                    (2.743, 1.905),
                    (2.286, 1.905),
                ]
            )
        ),
        Silkscreen(
            Polygon(
                [
                    (-2.667, 1.905),
                    (-2.667, 1.216),
                    (-2.21, 1.216),
                    (-2.21, 1.905),
                    (-2.667, 1.905),
                ]
            )
        ),
        Silkscreen(
            Polygon(
                [
                    (-2.667, -1.905),
                    (-2.667, -1.215),
                    (-2.21, -1.215),
                    (-2.21, -1.905),
                    (-2.667, -1.905),
                ]
            )
        ),
    ]
    custom_layer = [
        Custom(ArcPolyline(0.06, [Arc((-2.698, -1.8), 0.03, 0, -360)]), name="Fab")
    ]
    courtyard = Courtyard(rectangle(7.229, 3.962))
    model3d = Model3D(
        "littelfuse_SMBJ43CA.stp",
        position=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
        rotation=(0.0, 0.0, 0.0),
    )


class SymbolSMBJ43CA_C224021(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    A = Pin((2, 0), 2, Direction.Right)
    K = Pin((-2, 0), 2, Direction.Left)
    referecen = Text(">REF", 0.55559, Anchor.C).at((0, 2.77481))
    value = Text(">VALUE", 0.55559, Anchor.C).at((0, 1.9874))
    shapes = [
        Polyline(
            0.254,
            [(-0.4, 1.2), (-0.4, 1.2), (0, 1.2), (0, -1.2), (0.4, -1.2), (0.4, -1.2)],
        ),
        Polygon([(-2, 1), (0, 0), (-2, -1)]),
        Polygon([(2, 1), (0, 0), (2, -1)]),
    ]


class SMBJ43CA(Component):
    """
    Littelfuse SMBJ43CA 43V bidirectional TVS diode
    43V 600W bidirectional TVS diode for transient voltage suppression
    """

    name = "C224021"
    manufacturer = "Littelfuse"
    mpn = "SMBJ43CA"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Littelfuse-SMBJ43CA_C224021.pdf"
    reference_designator_prefix = "D"

    A = Port()
    """Anode terminal of the TVS diode"""
    K = Port()
    """Cathode terminal of the TVS diode"""

    landpattern = LandpatternSMB_L4_4_W3_6_LS5_4_BI()
    symbol = SymbolSMBJ43CA_C224021()

    mappings = [
        SymbolMapping({A: symbol.A, K: symbol.K}),
        PadMapping({A: landpattern.p[2], K: landpattern.p[1]}),
    ]


Device: type[SMBJ43CA] = SMBJ43CA
