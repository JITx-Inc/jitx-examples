"""
Microchip KSZ9031RNX Gigabit Ethernet Transceiver with RGMII
=============================================================

Component definition for the KSZ9031RNX 10/100/1000 Mbps Ethernet PHY in its
48-terminal 7 mm x 7 mm QFN packages, from the KSZ9031RNX data sheet
DS00002117K.

The ports carry the names of Table 2-1 ("Signals - KSZ9031RNX"). A pin with
more than one function (``RXD3/MODE3``, ``LED1/PHYAD0/PME_N1``) is one port
under the first name the table gives it; Table 2-2 ("Strap-In Options -
KSZ9031RNX") lists the strap-in function each of those pins also carries.
Names the table repeats (``DVDDL``, ``DVDDH``, ``AVDDL``, ``AVDDH``, ``NC``)
and numbered names (``TXD0`` to ``TXD3``, ``RXD0`` to ``RXD3``) are indexed
lists, in pin-number order. The exposed paddle is ``P_GND``.

The component carries no application circuit: the strap resistors, the 25 MHz
reference clock of Table 10-1, the supply decoupling and the exposed-pad thermal
vias (V and EV of Figures 13-3, 13-6 and 13-9) belong to the circuit that places
it. The two ``NC`` pins (13 and 47) are not bonded and are marked
``no_connect()``.

The orderable part follows the Product Identification System page of the data
sheet: ``temperature`` and ``package`` select one of its ordering examples.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, override

from jitx.component import Component
from jitx.landpattern import PadMapping
from jitx.net import Port
from jitx.shapes import Shape
from jitx.shapes.composites import rectangle
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.qfn import QFN, QFNLead
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.leads import LeadPlacement, LeadProfile
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig, WindowSubdivide
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row

Temperature = Literal["C", "I", "U", "V"]
"""Temperature code of the ordering number: C is 0 to +70 C, I is -40 to +85 C,
U is -40 to +85 C (automotive grade 3), V is -40 to +105 C (automotive grade 2)."""

BondWire = Literal["A", "B", "C"]
"""Bond-wire code of the ordering number: A is the PVA package (3.5 mm exposed
pad), B is the PUA package (5.05 mm exposed pad, wettable flanks), C is the PSA
package (5.05 mm exposed pad)."""

ORDERING_EXAMPLES: dict[tuple[Temperature, BondWire], str] = {
    ("C", "A"): "KSZ9031RNXCA",
    ("C", "C"): "KSZ9031RNXCC",
    ("I", "A"): "KSZ9031RNXIA",
    ("I", "C"): "KSZ9031RNXIC",
    ("U", "B"): "KSZ9031RNXUB-VAO",
    ("V", "B"): "KSZ9031RNXVB-VAO",
}
"""The ordering examples of the Product Identification System page, tray
packed. Examples f) and h) are the tape-and-reel (``TR``) codes of e) and g)."""


@dataclass(frozen=True)
class QFNPackageVariant:
    """Dimensions of one package drawing and its recommended land pattern."""

    name: str
    """Package code of the drawing."""

    terminal_width: Toleranced
    """b, terminal width."""

    terminal_length: Toleranced
    """L, terminal length."""

    exposed_pad: float
    """X2 and Y2, the recommended center pad width and length (maximum)."""

    contact_pad_length: float
    """Y1, the recommended contact pad length (maximum)."""


CONTACT_PAD_SPACING = 6.90
"""C1 and C2, the recommended contact pad center-to-center spacing, in every
land pattern figure (13-3, 13-6, 13-9)."""

CONTACT_PAD_WIDTH = 0.30
"""X1, the recommended contact pad width (maximum), in every land pattern
figure (13-3, 13-6, 13-9)."""

PITCH = 0.50
"""e, the terminal pitch (BSC), in every package drawing."""

BODY = Toleranced.exact(7.00)
"""D and E, the body length and width (BSC), in every package drawing."""

HEIGHT = Toleranced.min_typ_max(0.80, 0.90, 1.00)
"""A, the overall height, in every package drawing."""

PACKAGES: dict[BondWire, QFNPackageVariant] = {
    # Figure 13-2 (C04-1125-PVA dimensions) and Figure 13-3 (land pattern).
    "A": QFNPackageVariant(
        name="PVA",
        terminal_width=Toleranced.min_typ_max(0.18, 0.25, 0.30),
        terminal_length=Toleranced.min_typ_max(0.30, 0.40, 0.50),
        exposed_pad=3.60,
        contact_pad_length=0.85,
    ),
    # Figure 13-5 (C04-1263 dimensions) and Figure 13-6 (land pattern).
    # Figures 13-6 and 13-9 also give G1, contact pad to center pad, as
    # 0.43 mm minimum. C1 6.90 and Y1 0.90 put the contact pads' inner edges
    # 3.00 mm from center, so the 5.20 mm X2 maximum leaves 0.40 mm. The model
    # keeps X2, C1 and Y1 as published; a center pad of 5.14 mm or less would
    # meet G1.
    "B": QFNPackageVariant(
        name="PUA",
        terminal_width=Toleranced.min_typ_max(0.20, 0.25, 0.30),
        terminal_length=Toleranced.min_typ_max(0.35, 0.40, 0.45),
        exposed_pad=5.20,
        contact_pad_length=0.90,
    ),
    # Figure 13-8 (C04-1124 dimensions) and Figure 13-9 (land pattern).
    "C": QFNPackageVariant(
        name="PSA",
        terminal_width=Toleranced.min_typ_max(0.20, 0.25, 0.30),
        terminal_length=Toleranced.min_typ_max(0.35, 0.40, 0.45),
        exposed_pad=5.20,
        contact_pad_length=0.90,
    ),
}

EXPOSED_PAD_PASTE = WindowSubdivide(padding=0.25, gridShape=(2, 2))
"""Paste on the exposed pad. The data sheet gives no stencil, so the pad takes a
2 x 2 grid of windows 0.25 mm apart and 0.25 mm in from the copper: 1.425 mm
square windows (63% coverage) on the 3.60 mm pad and 2.225 mm square windows
(73% coverage) on the 5.20 mm pad."""


class RecommendedQFN(QFN):
    """QFN generator with the contact pads of a recommended land pattern.

    The generator sizes and spaces contact pads from the package's terminal
    dimensions by IPC-7351. This data sheet publishes its own land pattern, so
    each contact pad here is ``contact_pad`` (Y1 along the lead, X1 across it),
    centered ``contact_pad_spacing`` (C1, C2) from the pad opposite it. The
    package body, numbering, exposed pad, courtyard and silkscreen still come
    from the generator.
    """

    def __init__(
        self,
        *,
        num_leads: int,
        contact_pad: tuple[float, float],
        contact_pad_spacing: float,
        pitch: float,
    ) -> None:
        # The overrides below replace two private methods QFN inherits:
        # `_lead_placements` (the lead profile) and `_pad_rectangle`
        # (QuadColumnLeadShape). If a jitxlib-landpatterns release renames or
        # moves either, the override would be skipped without an error and the
        # pads would fall back to IPC sizing, so fail here instead.
        for name in ("_lead_placements", "_pad_rectangle"):
            if not callable(getattr(QFN, name, None)):
                raise TypeError(
                    f"QFN no longer has {name}; RecommendedQFN cannot apply "
                    "the data sheet's recommended land pattern"
                )
        super().__init__(num_leads=num_leads)
        self._recommended_placement = LeadPlacement(
            pad_size=contact_pad, center=contact_pad_spacing, pitch=pitch
        )

    @override
    def _lead_placements(self) -> Sequence[LeadPlacement]:
        return (self._recommended_placement,)

    @override
    def _pad_rectangle(self, width: float, height: float) -> Shape:
        return rectangle(*self._recommended_placement.pad_size)


def qfn_landpattern(variant: QFNPackageVariant) -> RecommendedQFN:
    """Build the recommended land pattern for one package variant."""
    return (
        RecommendedQFN(
            num_leads=48,
            contact_pad=(variant.contact_pad_length, CONTACT_PAD_WIDTH),
            contact_pad_spacing=CONTACT_PAD_SPACING,
            pitch=PITCH,
        )
        .lead_profile(
            LeadProfile(
                span=BODY,
                pitch=PITCH,
                type=QFNLead(
                    length=variant.terminal_length,
                    width=variant.terminal_width,
                ),
            )
        )
        .package_body(RectanglePackage(width=BODY, length=BODY, height=HEIGHT))
        .density_level(DensityLevel.B)
        .thermal_pad(
            rectangle(variant.exposed_pad, variant.exposed_pad),
            config=SMDPadConfig(paste=EXPOSED_PAD_PASTE),
        )
    )


class KSZ9031RNX(Component):
    """Microchip KSZ9031RNX gigabit Ethernet PHY with an RGMII MAC interface.

    Args:
        temperature: Temperature code of the ordering number (``Temperature``).
        package: Bond-wire code of the ordering number (``BondWire``), which
            selects the package drawing and land pattern.

    The default, ``KSZ9031RNXCA``, is ordering example a) of the data sheet.
    A combination that is not one of ``ORDERING_EXAMPLES`` raises
    ``ValueError``.
    """

    manufacturer = "Microchip Technology"
    # DS00002117K
    datasheet = "https://ww1.microchip.com/downloads/aemDocuments/documents/UNG/ProductDocuments/DataSheets/KSZ9031RNX-Data-Sheet-DS00002117.pdf"
    reference_designator_prefix = "U"

    # Media dependent interface, pins 2-3, 5-8, 10-11.
    TXRXP_A = Port()
    TXRXM_A = Port()
    TXRXP_B = Port()
    TXRXM_B = Port()
    TXRXP_C = Port()
    TXRXM_C = Port()
    TXRXP_D = Port()
    TXRXM_D = Port()

    # RGMII, pins 19-22, 24-25, 27-28, 31-33, 35.
    GTX_CLK = Port()
    """Pin 24, the RGMII TXC (transmit reference clock) input."""
    TX_EN = Port()
    """Pin 25, the RGMII TX_CTL (transmit control) input."""
    TXD = [Port() for _ in range(4)]
    """TXD0 to TXD3, pins 19 to 22."""
    RX_CLK = Port()
    """RX_CLK/PHYAD2, pin 35, the RGMII RXC (receive reference clock) output."""
    RX_DV = Port()
    """RX_DV/CLK125_EN, pin 33, the RGMII RX_CTL (receive control) output."""
    RXD = [Port() for _ in range(4)]
    """RXD0/MODE0 to RXD3/MODE3, pins 32, 31, 28 and 27."""

    # Management interface, pins 36-37.
    MDC = Port()
    MDIO = Port()

    # Control, LEDs and clock, pins 15, 17, 38, 41-42, 45-46, 48.
    LED1 = Port()
    """LED1/PHYAD0/PME_N1, pin 17."""
    LED2 = Port()
    """LED2/PHYAD1, pin 15."""
    INT_N = Port()
    """INT_N/PME_N2, pin 38."""
    CLK125_NDO = Port()
    """CLK125_NDO/LED_MODE, pin 41."""
    RESET_N = Port()
    XI = Port()
    XO = Port()
    ISET = Port()

    # Supplies, LDO controller and ground.
    AVDDH = [Port() for _ in range(2)]
    """Pins 1 and 12."""
    AVDDL = [Port() for _ in range(2)]
    """Pins 4 and 9."""
    AVDDL_PLL = Port()
    DVDDL = [Port() for _ in range(6)]
    """Pins 14, 18, 23, 26, 30 and 39."""
    DVDDH = [Port() for _ in range(3)]
    """Pins 16, 34 and 40."""
    LDO_O = Port()
    VSS = Port()
    P_GND = Port()
    """Exposed paddle on the bottom of the package."""

    NC = [Port() for _ in range(2)]
    """Pins 13 and 47, not bonded."""

    def __init__(self, temperature: Temperature = "C", package: BondWire = "A") -> None:
        mpn = ORDERING_EXAMPLES.get((temperature, package))
        if mpn is None:
            raise ValueError(
                f"KSZ9031RNX has no ordering code for temperature {temperature!r} "
                f"and package {package!r}; supported: "
                f"{', '.join(sorted(ORDERING_EXAMPLES.values()))}"
            )
        self.mpn = mpn
        self.package_variant = PACKAGES[package]
        self.landpattern = qfn_landpattern(self.package_variant)

        lp = self.landpattern
        self.mappings = [
            PadMapping(
                {
                    self.AVDDH[0]: lp.p[1],
                    self.TXRXP_A: lp.p[2],
                    self.TXRXM_A: lp.p[3],
                    self.AVDDL[0]: lp.p[4],
                    self.TXRXP_B: lp.p[5],
                    self.TXRXM_B: lp.p[6],
                    self.TXRXP_C: lp.p[7],
                    self.TXRXM_C: lp.p[8],
                    self.AVDDL[1]: lp.p[9],
                    self.TXRXP_D: lp.p[10],
                    self.TXRXM_D: lp.p[11],
                    self.AVDDH[1]: lp.p[12],
                    self.NC[0]: lp.p[13],
                    self.DVDDL[0]: lp.p[14],
                    self.LED2: lp.p[15],
                    self.DVDDH[0]: lp.p[16],
                    self.LED1: lp.p[17],
                    self.DVDDL[1]: lp.p[18],
                    self.TXD[0]: lp.p[19],
                    self.TXD[1]: lp.p[20],
                    self.TXD[2]: lp.p[21],
                    self.TXD[3]: lp.p[22],
                    self.DVDDL[2]: lp.p[23],
                    self.GTX_CLK: lp.p[24],
                    self.TX_EN: lp.p[25],
                    self.DVDDL[3]: lp.p[26],
                    self.RXD[3]: lp.p[27],
                    self.RXD[2]: lp.p[28],
                    self.VSS: lp.p[29],
                    self.DVDDL[4]: lp.p[30],
                    self.RXD[1]: lp.p[31],
                    self.RXD[0]: lp.p[32],
                    self.RX_DV: lp.p[33],
                    self.DVDDH[1]: lp.p[34],
                    self.RX_CLK: lp.p[35],
                    self.MDC: lp.p[36],
                    self.MDIO: lp.p[37],
                    self.INT_N: lp.p[38],
                    self.DVDDL[5]: lp.p[39],
                    self.DVDDH[2]: lp.p[40],
                    self.CLK125_NDO: lp.p[41],
                    self.RESET_N: lp.p[42],
                    self.LDO_O: lp.p[43],
                    self.AVDDL_PLL: lp.p[44],
                    self.XO: lp.p[45],
                    self.XI: lp.p[46],
                    self.NC[1]: lp.p[47],
                    self.ISET: lp.p[48],
                    self.P_GND: lp.thermal_pads[0],
                }
            )
        ]

        # One box for the supplies and one for the signals, each port once.
        self.symbols = [
            BoxSymbol(
                rows=Row(
                    left=[
                        PinGroup(*self.AVDDH, *self.AVDDL, self.AVDDL_PLL),
                        PinGroup(*self.DVDDH, *self.DVDDL),
                    ],
                    right=[PinGroup(self.LDO_O), PinGroup(*self.NC)],
                ),
                columns=Column(down=PinGroup(self.VSS, self.P_GND)),
            ),
            BoxSymbol(
                rows=Row(
                    left=[
                        PinGroup(
                            self.TXRXP_A,
                            self.TXRXM_A,
                            self.TXRXP_B,
                            self.TXRXM_B,
                            self.TXRXP_C,
                            self.TXRXM_C,
                            self.TXRXP_D,
                            self.TXRXM_D,
                        ),
                        PinGroup(self.ISET),
                        PinGroup(self.XI, self.XO),
                    ],
                    right=[
                        PinGroup(self.GTX_CLK, self.TX_EN, *self.TXD),
                        PinGroup(self.RX_CLK, self.RX_DV, *self.RXD),
                        PinGroup(self.MDC, self.MDIO),
                        PinGroup(
                            self.INT_N,
                            self.RESET_N,
                            self.CLK125_NDO,
                            self.LED1,
                            self.LED2,
                        ),
                    ],
                ),
            ),
        ]

        for nc in self.NC:
            nc.no_connect()


Device: type[KSZ9031RNX] = KSZ9031RNX
