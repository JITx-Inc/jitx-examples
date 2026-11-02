"""
Seiko Epson TSX-3225 Crystal Units
==================================

One component class for the TSX-3225 series: 16 MHz to 50 MHz fundamental
crystal units in a 3.2 mm x 2.5 mm x 0.6 mm four-pad package, from the Epson
FA-238V / FA-238 / TSX-3225 data sheet.

The data sheet asks for the load capacitance to be specified and lists the
frequency tolerance and frequency versus temperature characteristics as
per-order requirements, so the series has no ordering code that can be built
from those fields. Each orderable unit is instead a product number. The data
sheet prints it as ``X1E000021xxxx17``; the catalog numbers used here are the
thirteen-character ``X1E000021xxxx`` and omit that two-digit ``17`` suffix.
``TSX3225`` takes the specification fields as constructor arguments and looks
the product number up in ``seiko_epson_TSX_3225.csv``, the TSX-3225 rows of
Epson's product-search catalog
(https://download.epsondevice.com/td/ps/xtal_mhz.json). A combination the
catalog does not list raises ``ValueError``; a combination it lists under more
than one product number needs ``part_number=`` to choose one.

Pads 1 and 3 are the crystal; pads 2 and 4 are connected to the cover and go to
ground.
"""

import csv
import math
from dataclasses import dataclass
from functools import cache, partial
from importlib.resources import files

import eseries
import jitx
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.container import inline
from jitx.decorators import late
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Net, Port, ShortTrace
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.units import F
from jitxlib.parts import Capacitor


class CrystalComponent(Component):
    OSC1: Port = Port()
    OSC2: Port = Port()


class CrystalResonator(CrystalComponent):
    """A two-terminal crystal with the electrical parameters a load-capacitor
    calculation needs. ``shunt_capacitance`` and ``motional_capacitance`` are
    ``None`` when the manufacturer does not publish them."""

    load_capacitance: float
    shunt_capacitance: float | None
    motional_capacitance: float | None
    esr: float
    frequency: float
    frequency_tolerance: float
    max_drive_level: float

    def __init__(
        self,
        *,
        load_capacitance: float,
        shunt_capacitance: float | None,
        motional_capacitance: float | None,
        esr: float,
        frequency: float,
        frequency_tolerance: float,
        max_drive_level: float,
    ) -> None:
        self.load_capacitance = load_capacitance
        self.shunt_capacitance = shunt_capacitance
        self.motional_capacitance = motional_capacitance
        self.esr = esr
        self.frequency = frequency
        self.frequency_tolerance = frequency_tolerance
        self.max_drive_level = max_drive_level

    @late
    def __post_init_checks(self) -> None:
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

    def add_load_caps(
        self, gnd: Net, stray_capacitance: float = 5.0e-12
    ) -> tuple[Capacitor, Capacitor]:
        """Add a C0G load capacitor for each crystal pin to the current
        circuit, sized to the nearest E24 value of
        ``2 * (load_capacitance - stray_capacitance)``, and return both.

        Each capacitor's ``p1`` joins the crystal pin it serves through
        ``ShortTrace(cap.p1, <OSC1 or OSC2>)``, so placement and routing keep
        it close to that pin, and its ``p2`` joins ``gnd``.

        The returned capacitors already belong to the current circuit. Read
        them, but do not assign them to an attribute of the circuit as well:
        each would then be registered twice, and translating the design fails
        with "Child object ... encountered multiple times".
        """
        capacitance = eseries.find_nearest(
            eseries.E24, 2.0 * (self.load_capacitance - stray_capacitance)
        )
        cap_1 = Capacitor(
            capacitance=(capacitance) * F, temperature_coefficient_code="C0G"
        )
        cap_2 = Capacitor(
            capacitance=(capacitance) * F, temperature_coefficient_code="C0G"
        )
        jitx.current.circuit += [
            cap_1,
            cap_2,
            ShortTrace(cap_1.p1, self.OSC1),
            cap_1.p2 + gnd,
            ShortTrace(cap_2.p1, self.OSC2),
            cap_2.p2 + gnd,
        ]
        return cap_1, cap_2


@dataclass(frozen=True)
class CatalogEntry:
    """One row of ``seiko_epson_TSX_3225.csv``, in the catalog's units."""

    part_number: str
    frequency_mhz: float
    load_capacitance_pf: float
    tolerance_ppm: float
    stability_ppm: float
    temperature_min_c: float
    temperature_max_c: float
    esr_max_ohm: float
    drive_level_max_uw: float


@cache
def catalog() -> tuple[CatalogEntry, ...]:
    """The TSX-3225 product numbers Epson lists, with their specifications."""
    text = (
        files("jitxexamples.components.crystals") / "seiko_epson_TSX_3225.csv"
    ).read_text()
    return tuple(
        CatalogEntry(
            part_number=row["part_number"],
            frequency_mhz=float(row["frequency_mhz"]),
            load_capacitance_pf=float(row["load_capacitance_pf"]),
            tolerance_ppm=float(row["tolerance_ppm"]),
            stability_ppm=float(row["stability_ppm"]),
            temperature_min_c=float(row["temperature_min_c"]),
            temperature_max_c=float(row["temperature_max_c"]),
            esr_max_ohm=float(row["esr_max_ohm"]),
            drive_level_max_uw=float(row["drive_level_max_uw"]),
        )
        for row in csv.DictReader(text.splitlines())
    )


def _close(a: float, b: float) -> bool:
    """Equal to the six decimals the catalog prints, in the catalog's units."""
    return math.isclose(a, b, rel_tol=0.0, abs_tol=1e-6)


class RectangleSMDPad(Pad):
    shape = rectangle(1.4, 1.15)
    soldermask = Soldermask(rectangle(1.45, 1.2))
    paste = Paste(rectangle(1.45, 1.2))


Fab = partial(Custom, name="Fab")


class TSX3225Package(CrystalResonator):
    """The pins, symbol and recommended footprint every TSX-3225 unit shares.

    Pads 1 and 3 are the crystal (``OSC1``, ``OSC2``); pads 2 and 4 are
    connected to the cover (``GND1``, ``GND0``). A subclass supplies the
    electrical parameters, the part number and the data sheet.
    """

    manufacturer = "Seiko Epson"
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
        # The data sheet's recommended footprint: 1.4 mm x 1.15 mm pads on
        # 2.2 mm by 1.6 mm centers.
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

    def __init__(
        self,
        *,
        load_capacitance: float,
        shunt_capacitance: float | None,
        motional_capacitance: float | None,
        esr: float,
        frequency: float,
        frequency_tolerance: float,
        max_drive_level: float,
    ) -> None:
        super().__init__(
            load_capacitance=load_capacitance,
            shunt_capacitance=shunt_capacitance,
            motional_capacitance=motional_capacitance,
            esr=esr,
            frequency=frequency,
            frequency_tolerance=frequency_tolerance,
            max_drive_level=max_drive_level,
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


def _describe(entry: CatalogEntry) -> str:
    """One catalog row's specification, each field labeled."""
    return (
        f"CL {entry.load_capacitance_pf:g} pF, "
        f"tolerance +/-{entry.tolerance_ppm:g} ppm at +25 C, "
        f"stability +/-{entry.stability_ppm:g} ppm over "
        f"{entry.temperature_min_c:g} to {entry.temperature_max_c:g} C"
    )


class TSX3225(TSX3225Package):
    """Seiko Epson TSX-3225 crystal unit, 3.2 mm x 2.5 mm, selected by its
    specification.

    Args:
        frequency: nominal frequency in Hz.
        load_capacitance: load capacitance CL in farads.
        frequency_tolerance: frequency tolerance at +25 C, as a fraction
            (``10e-6`` for +/-10 ppm).
        frequency_stability: frequency versus temperature over
            ``temperature_range``, as a fraction.
        temperature_range: the range ``frequency_stability`` holds over, as
            (minimum, maximum) in degrees Celsius.
        part_number: the product number to use when the catalog lists the
            specification under more than one. It must be one of those.

    Raises:
        ValueError: the catalog lists no product number for the
            specification; lists several and ``part_number`` is not given; or
            ``part_number`` is not one the catalog lists for it.
    """

    datasheet = "https://download.epsondevice.com/td/pdf/brief/TSX-3225_en.pdf"

    frequency_stability: float
    temperature_range: tuple[float, float]

    def __init__(
        self,
        *,
        frequency: float,
        load_capacitance: float,
        frequency_tolerance: float,
        frequency_stability: float,
        temperature_range: tuple[float, float],
        part_number: str | None = None,
    ) -> None:
        low, high = temperature_range
        mhz = frequency / 1e6
        asked = (
            f"a TSX-3225 at {mhz:g} MHz, CL {load_capacitance / 1e-12:g} pF, "
            f"tolerance +/-{frequency_tolerance / 1e-6:g} ppm at +25 C, "
            f"stability +/-{frequency_stability / 1e-6:g} ppm over {low:g} to "
            f"{high:g} C"
        )
        matches = [
            entry
            for entry in catalog()
            if _close(entry.frequency_mhz, mhz)
            and _close(entry.load_capacitance_pf, load_capacitance / 1e-12)
            and _close(entry.tolerance_ppm, frequency_tolerance / 1e-6)
            and _close(entry.stability_ppm, frequency_stability / 1e-6)
            and _close(entry.temperature_min_c, low)
            and _close(entry.temperature_max_c, high)
        ]
        if not matches:
            listed = sorted(
                {_describe(e) for e in catalog() if _close(e.frequency_mhz, mhz)}
            )
            raise ValueError(
                f"Epson lists no product number for {asked}. "
                f"Listed at {mhz:g} MHz: {'; '.join(listed) or 'none'}"
            )
        numbers = [entry.part_number for entry in matches]
        if part_number is not None:
            if part_number not in numbers:
                raise ValueError(
                    f"{part_number} is not a product number Epson lists for "
                    f"{asked}; it lists {', '.join(numbers)}"
                )
            matches = [e for e in matches if e.part_number == part_number]
        if len(matches) > 1:
            raise ValueError(
                f"Epson lists several product numbers for {asked}: "
                f"{', '.join(numbers)}. Pass part_number= to choose one."
            )
        entry = matches[0]

        super().__init__(
            load_capacitance=load_capacitance,
            shunt_capacitance=None,
            motional_capacitance=None,
            esr=entry.esr_max_ohm,
            frequency=frequency,
            frequency_tolerance=frequency_tolerance,
            max_drive_level=entry.drive_level_max_uw * 1e-6,
        )
        self.frequency_stability = frequency_stability
        self.temperature_range = (low, high)
        self.mpn = entry.part_number


class TSX_3225_32_0000MF10Z_W6(TSX3225Package):
    """32 MHz +/-10 ppm crystal, 12 pF, 40 ohms, ordered by its distributor
    code. Its values come from the distributor's data sheet. No source here
    ties the distributor code to one of the catalog's product numbers, so the
    unit takes no catalog row and has no ``frequency_stability`` or
    ``temperature_range``."""

    mpn = "TSX-3225 32.0000MF10Z-W6"
    datasheet = "https://datasheet.lcsc.com/lcsc/2201301130_Seiko-Epson-TSX-3225-32-0000MF10Z-W6_C1986412.pdf"

    def __init__(self) -> None:
        super().__init__(
            load_capacitance=12e-12,
            shunt_capacitance=1.31e-12,
            motional_capacitance=4.41e-15,
            esr=40,
            frequency=32.0e6,
            frequency_tolerance=10.0e-6,
            max_drive_level=100.0e-6,
        )


Device: type[TSX_3225_32_0000MF10Z_W6] = TSX_3225_32_0000MF10Z_W6
