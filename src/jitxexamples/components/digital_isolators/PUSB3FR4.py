"""Nexperia PUSB3FR4, 4-channel ESD protection for high-speed interfaces.

Source: Nexperia, "PUSB3FR4 ESD protection for ultra high-speed interfaces",
Product data sheet, 12 July 2018,
https://assets.nexperia.com/documents/data-sheet/PUSB3FR4.pdf (read from the
copy LCSC serves for part C294620,
https://datasheet.lcsc.com/datasheet/pdf/973b1dae6d18992ab9432880e89c8003.pdf?productCode=C294620).

Pinning (Table 1): pin 1 CH1, 2 CH2, 3 GND, 4 CH3, 5 CH4, 8 GND; pins 6, 7, 9
and 10 are "n.c.", not connected inside the package. Each pin is its own port,
the n.c. pins as ``NC6``, ``NC7``, ``NC9`` and ``NC10``. The part is a
"pass-through" design (Section 2, Fig. 15): each channel's trace runs under the
package across the channel pin and the n.c. pin opposite it (CH1 with 10, CH2
with 9, CH3 with 7, CH4 with 6). That join is board copper, not part of the
component, so the circuit using the part nets each pair; there is no internal
path for a pin model to describe.

The two GND pins are one port: they are the same node inside the package.

Land pattern: the reflow soldering footprint of Fig. 17 (DFN2510A-10,
SOT1176-1): pitch P 0.5, land width D 0.2, land length C 0.475, inner row gap
By 0.3, outer extent Ay 1.25, solder resist 0.05 beyond each land, occupied
area Hx 2.45 by Hy 1.5. Fig. 17 draws solder paste over the whole land.
Package body 2.5 by 1.0 (Fig. 16, nominal).
"""

from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.feature import Courtyard, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Polyline, Text
from jitxlib.symbols.box import BoxSymbol, PinGroup, Row

# Fig. 17, reflow soldering footprint, dimensions in mm.
PITCH = 0.5  # P
LAND_WIDTH = 0.2  # D
LAND_LENGTH = 0.475  # C
ROW_GAP = 0.3  # By, edge to edge between the two rows of lands
RESIST_MARGIN = 0.05  # solder resist beyond each land edge
OCCUPIED_X = 2.45  # Hx
OCCUPIED_Y = 1.5  # Hy
ROW_Y = (ROW_GAP + LAND_LENGTH) / 2  # 0.3875, land centre from package centre

# Fig. 16, package outline, nominal body.
BODY_X = 2.5
BODY_Y = 1.0


class DFNLand(Pad):
    """One DFN2510A-10 land, Fig. 17."""

    shape = rectangle(LAND_WIDTH, LAND_LENGTH)
    paste = Paste(rectangle(LAND_WIDTH, LAND_LENGTH))
    soldermask = Soldermask(
        rectangle(LAND_WIDTH + 2 * RESIST_MARGIN, LAND_LENGTH + 2 * RESIST_MARGIN)
    )


class DFN2510A10(Landpattern):
    """DFN2510A-10 (SOT1176-1) land pattern, top view as in Table 1: pins 1 to 5
    along the bottom row from left to right, pins 6 to 10 along the top row
    from right to left, so pin 10 sits opposite pin 1."""

    def __init__(self) -> None:
        self.p = {
            n: DFNLand().at(x, y)
            for n, (x, y) in {
                **{i + 1: (-2 * PITCH + i * PITCH, -ROW_Y) for i in range(5)},
                **{10 - i: (-2 * PITCH + i * PITCH, ROW_Y) for i in range(5)},
            }.items()
        }
        # Fig. 17's occupied area, widened where the body (Fig. 16) is wider.
        self.courtyard = Courtyard(
            rectangle(max(OCCUPIED_X, BODY_X), max(OCCUPIED_Y, BODY_Y))
        )
        # Silkscreen only off the lands: the two short ends and a pin 1 dot.
        sx = BODY_X / 2 + 0.1
        sy = BODY_Y / 2
        self.silkscreen = [
            Silkscreen(Polyline(0.1, [(-sx, -sy), (-sx, sy)])),
            Silkscreen(Polyline(0.1, [(sx, -sy), (sx, sy)])),
            Silkscreen(Circle(radius=0.08).at(-sx - 0.2, -ROW_Y)),
        ]
        self.ref_text = Silkscreen(Text(">REF", 0.5, Anchor.C).at(0.0, 1.2))


class PUSB3FR4(Component):
    """Nexperia PUSB3FR4 4-channel ESD protection, DFN2510A-10.

    For the pass-through layout, net each channel to the n.c. pin opposite it;
    see the module docstring."""

    manufacturer = "Nexperia"
    mpn = "PUSB3FR4"
    reference_designator_prefix = "U"
    datasheet = "https://assets.nexperia.com/documents/data-sheet/PUSB3FR4.pdf"

    CH1 = Port()
    CH2 = Port()
    GND = Port()
    CH3 = Port()
    CH4 = Port()
    NC6 = Port()
    """n.c., opposite CH4."""
    NC7 = Port()
    """n.c., opposite CH3."""
    NC9 = Port()
    """n.c., opposite CH2."""
    NC10 = Port()
    """n.c., opposite CH1."""

    def __init__(self) -> None:
        self.landpattern = DFN2510A10()
        self.symbol = BoxSymbol(
            rows=[
                Row(
                    left=[PinGroup([self.CH1, self.CH2, self.GND, self.CH3, self.CH4])],
                    right=[PinGroup([self.NC10, self.NC9, self.NC7, self.NC6])],
                )
            ]
        )
        lp = self.landpattern
        self.mappings = [
            PadMapping(
                {
                    self.CH1: lp.p[1],
                    self.CH2: lp.p[2],
                    self.GND: [lp.p[3], lp.p[8]],
                    self.CH3: lp.p[4],
                    self.CH4: lp.p[5],
                    self.NC6: lp.p[6],
                    self.NC7: lp.p[7],
                    self.NC9: lp.p[9],
                    self.NC10: lp.p[10],
                }
            ),
        ]


Device: type[PUSB3FR4] = PUSB3FR4
