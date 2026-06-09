from functools import partial
import eseries
import jitx
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.container import inline
from jitx.decorators import late
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Net, Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polyline, Text
from jitx.symbol import Pin, Symbol, Direction, SymbolMapping

from jitxlib.parts import Capacitor


class CrystalComponent(Component):
    OSC1: Port = Port()
    OSC2: Port = Port()


class CrystalResonator(CrystalComponent):
    load_capacitance: float
    shunt_capacitance: float
    motional_capacitance: float
    esr: float
    frequency: float
    frequency_tolerance: float
    max_drive_level: float

    def __init__(
        self,
        *,
        load_capacitance: float,
        shunt_capacitance: float,
        motional_capacitance: float,
        esr: float,
        frequency: float,
        frequency_tolerance: float,
        max_drive_level: float,
    ):
        self.load_capacitance = load_capacitance
        self.shunt_capacitance = shunt_capacitance
        self.motional_capacitance = motional_capacitance
        self.esr = esr
        self.frequency = frequency
        self.frequency_tolerance = frequency_tolerance
        self.max_drive_level = max_drive_level

    @late
    def __post_init_checks(self):
        for fieldname in [
            "load_capacitance",
            "shunt_capacitance",
            "motional_capacitance",
            "esr",
            "frequency",
            "frequency_tolerance",
            "max_drive_level",
        ]:
            if not hasattr(self, fieldname):
                raise ValueError(f"{fieldname} is required")

    def add_load_caps(self, gnd: Net, stray_capacitance=5.0e-12):
        capacitance = eseries.find_nearest(
            eseries.E24, 2.0 * (self.load_capacitance - stray_capacitance)
        )
        jitx.current.circuit += [
            Capacitor(
                capacitance=capacitance, temperature_coefficient_code="C0G"
            ).insert(self.OSC1, gnd),
            Capacitor(
                capacitance=capacitance, temperature_coefficient_code="C0G"
            ).insert(self.OSC2, gnd),
        ]


class RectangleSMDPad(Pad):
    shape = rectangle(1.4, 1.15)
    soldermask = Soldermask(rectangle(1.45, 1.2))
    paste = Paste(rectangle(1.45, 1.2))


Fab = partial(Custom, name="Fab")


class TSX_3225_32_0000MF10Z_W6(CrystalResonator):
    """32 MHz ±10ppm Crystal 12pF 40 Ohms 4-SMD, No Lead"""

    manufacturer = "Seiko Epson"
    mpn = "TSX-3225 32.0000MF10Z-W6"
    datasheet = "https://datasheet.lcsc.com/lcsc/2201301130_Seiko-Epson-TSX-3225-32-0000MF10Z-W6_C1986412.pdf"
    reference_designator_prefix = "X"

    GND0 = Port()
    GND1 = Port()

    @inline
    class symbol(Symbol):
        pin_name_size = 1
        pad_name_size = 1

        GND0 = Pin(at=(-4, 2), direction=Direction.Left, length=2)
        GND1 = Pin(at=(4, -2), direction=Direction.Right, length=2)
        OSC1 = Pin(at=(-4, -2), direction=Direction.Left, length=2)
        OSC2 = Pin(at=(4, 2), direction=Direction.Right, length=2)

        value = Text(">VALUE", 0.55, anchor=Anchor.C).at(0, 2.78)
        reference = Text(">REF", 0.55, anchor=Anchor.C).at(0, 3.57)
        foreground = [
            rectangle(8, 8),
            Polyline(0.2, [(-1, -0.8), (-1, 0.8)]),
            Polyline(0.2, [(0.6, -1.4), (-0.6, -1.4)]),
            Polyline(0.2, [(1, -0.8), (1, 0.8)]),
            Polyline(0.2, [(-0.6, -1.4), (-0.6, 1.4), (0.6, 1.4), (0.6, -1.4)]),
            Polyline(0.2, [(4, 2), (2, 2), (2, 0), (1.2, 0)]),
            Polyline(0.2, [(-4, -2), (-2, -2), (-2, 0), (-1.2, 0)]),
            Polyline(0.2, [(1, -1.4), (1, 1.4)]),
            Polyline(0.2, [(-1, -1.4), (-1, 1.4)]),
            Polyline(
                0.2, [(0.6, 1.4), (0.6, -1.4), (-0.6, -1.4), (-0.6, 1.4), (0.6, 1.4)]
            ),
        ]

    @inline
    class landpattern(Landpattern):
        p = {
            1: RectangleSMDPad().at(-1.1, -0.8),
            2: RectangleSMDPad().at(1.1, -0.8),
            3: RectangleSMDPad().at(1.1, 0.8),
            4: RectangleSMDPad().at(-1.1, 0.8),
        }

        labels = [
            Silkscreen(Text(">REF", 0.5, Anchor.W).at(-0.75, 3.575)),
            Fab(Text(">VALUE", 0.5, Anchor.W).at(-0.75, 2.575)),
        ]

        silkscreens = [
            Silkscreen(
                Polyline(
                    0.152,
                    [(-2, -1.5), (-2, 1.5), (2, 1.5), (2, -1.5), (-2, -1.5)],
                )
            ),
            Silkscreen(Polyline(0.152, [(-2.1, -0.1), (-2.1, -1.6), (-0.1, -1.6)])),
        ]

        fab_drawings = [
            Fab(ArcPolyline(0.06, [Arc((-1.486, -1.136), 0.03, 0, -360)])),
            Fab(ArcPolyline(0.36, [Arc((-1.029, -0.775), 0.18, 0, -360)])),
        ]

        courtyard = Courtyard(rectangle(4, 3))

    def __init__(self):
        super().__init__(
            load_capacitance=12e-12,
            shunt_capacitance=1.31e-12,
            motional_capacitance=4.41e-15,
            esr=40,
            frequency=32.0e6,
            frequency_tolerance=10.0e-6,
            max_drive_level=100.0e-6,
        )

        self.mappings = [
            PadMapping(
                {
                    self.GND0: self.landpattern.p[4],
                    self.GND1: self.landpattern.p[2],
                    self.OSC1: self.landpattern.p[1],
                    self.OSC2: self.landpattern.p[3],
                }
            ),
            SymbolMapping(
                {
                    self.GND0: self.symbol.GND0,
                    self.GND1: self.symbol.GND1,
                    self.OSC1: self.symbol.OSC1,
                    self.OSC2: self.symbol.OSC2,
                }
            ),
        ]


Device: type[TSX_3225_32_0000MF10Z_W6] = TSX_3225_32_0000MF10Z_W6
