"""
60312202114514 / WR-SMA end launch jack
=======================================

This module provides a component definition for the Würth Elektronik
60312202114514, a WR-SMA 50 ohm end launch jack with a flat centre tab, for a
1.6 mm board.

The land pattern comes from the recommended land pattern of the Würth
datasheet drawing, revision 001.001. All dimensions are in mm:

- centre pad 0.61 +/-0.05 wide and at least 1.97 long, from the board end;
- ground pads 9.9 +/-0.05 outer and 7.1 +/-0.05 inner overall width, 5.0
  +/-0.05 long, on the top and on the bottom of the board.

The land pattern has no ground vias. The drawing gives the part as 50 ohm from
DC to 18 GHz, with VSWR 1.2 and insertion loss 0.14 dB at most up to
12.4 GHz, and notes that "The VSWR in application varies decisively according
to PCB layout".

The land pattern's frame is the frame of the vendor's HFSS model
(``HFSS_MODEL_URL``): x = 0 is the body face, which sits on the board edge,
+x runs into the board along the centre pad, and the pads are centred on
y = 0. Place the part with its origin on the board edge and its +x axis
pointing into the board.

The courtyard, on the top and on the bottom, covers what sits on the board:
the pads, and the shell's ground tabs, which the vendor model puts at x 0 to
4.76 within the body's 9.52 mm width. It starts at the board edge, since the
body behind the face hangs off the board.
"""

from __future__ import annotations

from jitx.component import Component
from jitx.feature import Courtyard
from jitx.landpattern import Landpattern, PadMapping
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitxlib.landpatterns.pads import SMDPad
from jitxlib.symbols.box import BoxSymbol

CENTER_PAD_WIDTH = 0.61
"""Datasheet recommended land pattern: centre pad 0.61 +/-0.05 wide."""

CENTER_PAD_LENGTH = 1.97
"""Datasheet recommended land pattern: centre pad 1.97 minimum from the PCB
end."""

GROUND_OUTER = 9.9
"""Datasheet recommended land pattern: ground pads 9.9 +/-0.05 outer overall
width."""

GROUND_INNER = 7.1
"""Datasheet recommended land pattern: ground pads 7.1 +/-0.05 inner overall
width."""

GROUND_LENGTH = 5.0
"""Datasheet recommended land pattern: ground pads 5.0 +/-0.05 long, top and
bottom."""

BODY_WIDTH = 9.52
"""Datasheet: body 9.52 by 7.92; the vendor model spans y -4.76 to 4.76, so
9.52 is the width across the board edge."""

TAB_REACH = 4.76
"""Vendor model (``HFSS_MODEL_URL``): the shell's ground tabs reach x = 4.76
into the board."""

COURTYARD_EXCESS = 0.25
"""Courtyard margin beyond the pads and tabs, in mm, as the Molex and
Weidmuller connectors in this package use."""

HFSS_MODEL_URL = (
    "https://www.we-online.com/components/products/download/"
    "ANSYS_60312202114514%20%28rev25a%29.a3dcomp"
)
"""The vendor's HFSS 3D component (``.a3dcomp``) for this part, rev25a,
kept for later use: nothing in this repository downloads or reads it yet.
The file was recorded by 2026-11-05 as 390,182 bytes, with the SHA-256 in
``HFSS_MODEL_SHA256``; check a download against both. Its native frame is
the land pattern's frame: x = 0 at the body face on the board edge, +x into
the board, and z = 0 on the top copper."""

HFSS_MODEL_SHA256 = "54cdf702be7343e09a787fa0de413e77984569b4b6bcdddee27d8adccfc90959"
"""SHA-256 of the rev25a file at ``HFSS_MODEL_URL``, to check a download
against."""

_GROUND_PAD_WIDTH = (GROUND_OUTER - GROUND_INNER) / 2
_GROUND_PAD_Y = (GROUND_OUTER + GROUND_INNER) / 4


class WurthLaunchLandpattern(Landpattern):
    """The centre pad, and a ground pad on each side of it on the top and on
    the bottom of the board, each with a soldermask opening and paste, and a
    courtyard on each side."""

    def __init__(self) -> None:
        self.sig = SMDPad(rectangle(CENTER_PAD_LENGTH, CENTER_PAD_WIDTH)).at(
            CENTER_PAD_LENGTH / 2, 0.0
        )
        self.gnd = [
            SMDPad(rectangle(GROUND_LENGTH, _GROUND_PAD_WIDTH)).at(
                GROUND_LENGTH / 2, y, on=side
            )
            for side in (Side.Top, Side.Bottom)
            for y in (_GROUND_PAD_Y, -_GROUND_PAD_Y)
        ]
        reach = max(GROUND_LENGTH, TAB_REACH) + COURTYARD_EXCESS
        half = max(GROUND_OUTER, BODY_WIDTH) / 2 + COURTYARD_EXCESS
        self.courtyard = [
            Courtyard(rectangle(reach, 2 * half).at(reach / 2, 0.0), side=side)
            for side in (Side.Top, Side.Bottom)
        ]


class Wurth60312202114514(Component):
    """Würth Elektronik WR-SMA 60312202114514, 50 ohm end launch jack, flat
    tab, for a 1.6 mm board."""

    manufacturer = "Würth Elektronik"
    mpn = "60312202114514"
    datasheet = (
        "https://www.we-online.com/components/products/datasheet/60312202114514.pdf"
    )
    reference_designator_prefix = "J"

    sig = Port()
    """The centre pin."""
    gnd = Port()
    """The shell: all four ground pads."""

    def __init__(self) -> None:
        self.landpattern = WurthLaunchLandpattern()
        self.symbol = BoxSymbol()
        self.mappings = [
            PadMapping({self.sig: self.landpattern.sig, self.gnd: self.landpattern.gnd})
        ]


Device: type[Wurth60312202114514] = Wurth60312202114514
