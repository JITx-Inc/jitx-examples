"""
onsemi NTF6P02T3G P-Channel MOSFET
==================================

A -20 V, -10 A P-channel MOSFET in SOT-223 (CASE 318E, STYLE 3), from the onsemi
data sheet NTF6P02T3/D. Pin 1 is the gate, pin 2 the drain, pin 3 the source and
pin 4, the tab, the drain again. The component has one port per pad: ``G``,
``S`` and ``D``, a list of the two drain pads, ``D[0]`` on pin 2 and ``D[1]`` on
the tab.

Facts from the data sheet that no JITX field holds:

- Maximum ratings: VDSS -20 V, VGS +/-8 V, ID -10 A continuous at 25 C and
  -8.4 A at 70 C, junction temperature -55 to +150 C.
- Thermal resistance: 15 C/W junction to lead; 71.4 C/W junction to ambient in
  steady state on FR4 with a 1 inch drain pad, 1.127 square inches of copper
  (Note 2); 160 C/W on the minimum recommended pad (Note 3), which still
  assumes 0.412 square inches of copper, about 16 times the 16.6 square
  millimetres of this footprint's own pads.
- Gate threshold VGS(th) at 250 uA: -0.4 V minimum, -0.7 V typical, -1.0 V
  maximum, with a 2.6 mV/C temperature coefficient that lowers its magnitude
  as the part heats.
- RDS(on): 44 mOhm typical and 50 mOhm maximum at VGS -4.5 V; 57 mOhm typical
  and 70 mOhm maximum at VGS -2.5 V.
- Input capacitance Ciss: 900 pF typical and 1200 pF maximum at VDS -16 V.

The land pattern is the data sheet's recommended footprint (page 7): three
1.50 mm by 2.00 mm lead pads at 2.30 mm pitch and a 3.80 mm by 2.00 mm tab
pad, with 6.30 mm between the lead row's center and the tab pad's center. The
data sheet gives no solder mask or paste expansion, so both match the pad and
the fabricator's rules set any expansion. The courtyard is 0.25 mm beyond the
larger of the pads and the body at its maximum size (D 6.70 mm, He 7.30 mm),
the IPC-7351 level B courtyard excess; the data sheet gives no courtyard.

The data sheet's own "NTF6P02T3" names the part family; NTF6P02T3G is the
orderable, lead-free part number. The component leaves ``value`` unset.
"""

from functools import partial

from jitx.anchor import Anchor
from jitx.circuit import Circuit
from jitx.component import Component as JITXComponent
from jitx.container import inline
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping

Fab = partial(Custom, name="Fab")

# The recommended footprint, page 7 of the data sheet.
LEAD_PAD = (1.50, 2.00)
TAB_PAD = (3.80, 2.00)
PITCH = 2.30
ROW_TO_TAB = 6.30
# 0.25 mm beyond the outermost copper or body edge on each side. The pads reach
# 4.15 mm from center in y (6.30 / 2 + 2.00 / 2) and 3.05 mm in x; the body at
# D max 6.70 mm reaches 3.35 mm in x.
COURTYARD = (2 * (6.70 / 2 + 0.25), 2 * (ROW_TO_TAB / 2 + 2.00 / 2 + 0.25))


class LeadPad(Pad):
    shape = rectangle(*LEAD_PAD)
    soldermask = Soldermask(rectangle(*LEAD_PAD))
    paste = Paste(rectangle(*LEAD_PAD))


class TabPad(Pad):
    shape = rectangle(*TAB_PAD)
    soldermask = Soldermask(rectangle(*TAB_PAD))
    paste = Paste(rectangle(*TAB_PAD))


class Component(JITXComponent):
    """The NTF6P02T3G itself: gate on pin 1, drain on pin 2 and the tab (pin 4),
    source on pin 3."""

    manufacturer = "onsemi"
    mpn = "NTF6P02T3G"
    reference_designator_prefix = "Q"
    datasheet = "https://www.onsemi.com/pdf/datasheet/ntf6p02t3-d.pdf"

    G = Port()
    S = Port()
    D = [Port(), Port()]
    """``D[0]`` is pin 2; ``D[1]`` is the tab, pin 4."""

    @inline
    class landpattern(Landpattern):
        p = {
            1: LeadPad().at(-PITCH, -ROW_TO_TAB / 2),
            2: LeadPad().at(0, -ROW_TO_TAB / 2),
            3: LeadPad().at(PITCH, -ROW_TO_TAB / 2),
            4: TabPad().at(0, ROW_TO_TAB / 2),
        }

        labels = [
            Silkscreen(Text(">REF", 0.5, Anchor.W).at(-3.0, 5.0)),
            Fab(Text(">VALUE", 0.5, Anchor.W).at(-3.0, -5.0)),
        ]

        # The body outline at nominal size (D 6.50 mm, E 3.50 mm), drawn on the
        # sides the pads leave clear, and a pin 1 mark beside pad 1.
        silkscreens = [
            Silkscreen(Polyline(0.15, [(-3.25, -1.0), (-3.25, 1.0)])),
            Silkscreen(Polyline(0.15, [(3.25, -1.0), (3.25, 1.0)])),
            Silkscreen(Polyline(0.15, [(-3.4, -2.2), (-3.4, -4.1)])),
        ]

        fab_drawings = [Fab(Polyline(0.1, [(-3.25, -1.75), (3.25, -1.75)]))]

        courtyard = Courtyard(rectangle(*COURTYARD))

    @inline
    class symbol(Symbol):
        pin_name_size = 0.7874
        pad_name_size = 0.7874

        G = Pin(at=(-4, 0), direction=Direction.Left, length=2)
        S = Pin(at=(4, 2), direction=Direction.Right, length=2)
        D2 = Pin(at=(4, 0), direction=Direction.Right, length=2)
        D4 = Pin(at=(4, -2), direction=Direction.Right, length=2)

        reference = Text(">REF", 0.55559, Anchor.C).at(0, 4.87481)
        value = Text(">VALUE", 0.55559, Anchor.C).at(0, 4.08741)
        foreground = [rectangle(8, 8)]

    def __init__(self) -> None:
        self.mappings = [
            PadMapping(
                {
                    self.G: self.landpattern.p[1],
                    self.D[0]: self.landpattern.p[2],
                    self.S: self.landpattern.p[3],
                    self.D[1]: self.landpattern.p[4],
                }
            ),
            SymbolMapping(
                {
                    self.G: self.symbol.G,
                    self.S: self.symbol.S,
                    self.D[0]: self.symbol.D2,
                    self.D[1]: self.symbol.D4,
                }
            ),
        ]


class NTF6P02T3G(Circuit):
    """The NTF6P02T3G with its two drain pads joined: ports ``g``, ``s`` and
    ``d``, and the part itself as ``mosfet``. A short trace or a copper area
    that must land on one drain pad names it on ``mosfet``: ``mosfet.D[1]`` is
    the tab, which carries the 71.4 C/W rating's copper."""

    d = Port()
    g = Port()
    s = Port()

    def __init__(self) -> None:
        self.mosfet = Component()
        self.D = self.d + self.mosfet.D[0] + self.mosfet.D[1]
        self.G = self.g + self.mosfet.G
        self.S = self.s + self.mosfet.S


Device: type[NTF6P02T3G] = NTF6P02T3G
