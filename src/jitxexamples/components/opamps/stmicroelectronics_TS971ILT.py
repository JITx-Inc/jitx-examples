from jitx.anchor import Anchor
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.container import inline
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import ArcPolyline, Arc, Polyline, Text
from jitx.symbol import SymbolMapping
from jitxlib.symbols.opamp import OpAmpSymbol


class RectanglePad(Pad):
    shape = rectangle(1, 0.6)
    soldermask = Soldermask(rectangle(1.102, 0.702))
    paste = Paste(rectangle(1.102, 0.702))


class OpAmp(Port):
    INp = Port()
    INn = Port()
    OUT = Port()


class TS971ILT(Circuit):
    """Single Rail-to-Rail Op-Amp in SOT23-5"""

    @inline
    class IC(Component):
        manufacturer = "STMicroelectronics"
        mpn = "TS971ILT"
        datasheet = "https://datasheet.lcsc.com/lcsc/2304140030_STMicroelectronics-TS971ILT_C2802553.pdf"
        reference_designator_prefix = "U"

        OUT = Port()
        VCC = Port()
        INn = Port()
        INp = Port()
        VDD = Port()

        @inline
        class landpattern(Landpattern):
            p = {
                1: RectanglePad().at(1.3, -0.95),
                2: RectanglePad().at(1.3, 0),
                3: RectanglePad().at(1.3, 0.95),
                4: RectanglePad().at(-1.3, 0.95),
                5: RectanglePad().at(-1.3, -0.95),
            }

            silkscreens = [
                Silkscreen(Text(">REF", 0.5, Anchor.W).at(-0.75, 3.383)),
                Silkscreen(Polyline(0.254, [(-0.9, -1.55), (0.9, -1.55)])),
                Silkscreen(Polyline(0.254, [(-0.9, -0.4), (-0.9, 0.4)])),
                Silkscreen(Polyline(0.254, [(-0.9, 1.55), (0.9, 1.55)])),
                Silkscreen(ArcPolyline(0.254, [Arc((1.524, -1.651), 0.127, 0, -360)])),
            ]

            custom_fabs = [
                Custom(Text(">VALUE", 0.5, Anchor.W).at(-0.75, 2.383), name="Fab"),
                Custom(
                    ArcPolyline(0.060, [Arc((1.4, -1.45), 0.03, 0, -360)]),
                    name="Fab",
                ),
                Custom(
                    ArcPolyline(0.4, [Arc((1.397, -1.016), 0.2, 0, -360)]),
                    name="Fab",
                ),
            ]

            courtyard = Courtyard(rectangle(3.702, 3.354))

        symbol = OpAmpSymbol()

        mappings = [
            PadMapping(
                {
                    OUT: landpattern.p[1],
                    VCC: landpattern.p[5],
                    INn: landpattern.p[4],
                    INp: landpattern.p[3],
                    VDD: landpattern.p[2],
                }
            ),
            SymbolMapping(
                {
                    OUT: symbol.OUT,
                    VCC: symbol.Vp,
                    INn: symbol.INn,
                    INp: symbol.INp,
                    VDD: symbol.Vn,
                }
            ),
        ]

    supply = Power()
    amp = OpAmp()

    def __init__(self):
        self.nets = [
            self.supply.Vp + self.IC.VCC,
            self.supply.Vn + self.IC.VDD,
            self.amp.INp + self.IC.INp,
            self.amp.INn + self.IC.INn,
            self.amp.OUT + self.IC.OUT,
        ]


Device: type[TS971ILT] = TS971ILT
