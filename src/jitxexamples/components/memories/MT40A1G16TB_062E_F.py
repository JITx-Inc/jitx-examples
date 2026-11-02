"""Micron MT40A1G16TB-062E:F DDR4 SDRAM.

16 Gb, x16, in a 96-ball split FBGA at 0.8 mm pitch.

The pin map and landpattern were carried over from
``JITx-Inc/jitx-protocols-ext`` (commit 33501cb,
``examples/protocols/memory/MT40A1G16TB_062E_F.py``), itself a translation of
the JITX Stanza model ``MT40A1G16TB-062E-F.stanza``. They have not been
rechecked against the Micron datasheet in this port; check the ball map against
the datasheet before ordering a board.

:py:mod:`jitxexamples.protocols.memory.ddr4_example` connects this part to a
DDR4 controller.
"""

from collections.abc import Iterable

from jitx import PadMapping
from jitx.component import Component
from jitx.net import Port
from jitx.shapes.primitive import Circle
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitxlib.landpatterns.courtyard import ExcessCourtyard
from jitxlib.landpatterns.grid_layout import (
    A1,
    AlphaDictNumbering,
    GridLandpatternGenerator,
    GridPosition,
)
from jitxlib.landpatterns.grid_planner import GridPlannerMixin
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import GridPadShapeGeneratorMixin, SMDPadConfig
from jitxlib.landpatterns.silkscreen.marker import Pad1Marker
from jitxlib.landpatterns.silkscreen.outlines import SilkscreenOutline
from jitxlib.symbols.box import BoxSymbol

from jitxexamples.protocols.memory.ddr4 import DDR4, DDR4Rank, DDR4Width


class SplitBGABase(
    GridPlannerMixin,
    GridPadShapeGeneratorMixin,
    GridLandpatternGenerator,
):
    """Split BGA: two three-column halves separated by a gap."""

    def __init__(
        self,
        num_rows: int = 16,
        half_cols: int = 3,
        ball_diameter: float = 0.42,
        pitch: float = 0.80,
        gap: float = 3.20,
    ) -> None:
        super().__init__()
        self._num_rows = num_rows
        self._half_cols = half_cols
        self._num_cols = 9
        self._pitch = pitch
        self._gap = gap
        self.pad_shape(Circle(diameter=ball_diameter))

    def _generate_layout(self) -> Iterable[GridPosition]:
        half_offset = ((self._half_cols - 1) * self._pitch + self._gap) / 2.0
        center_row = (self._num_rows - 1) / 2.0
        half_center_col = (self._half_cols - 1) / 2.0

        for r in range(self._num_rows):
            row_y = (center_row - r) * self._pitch

            for c in range(self._half_cols):
                x = (c - half_center_col) * self._pitch - half_offset
                tx = Transform.translate(x, row_y)
                yield GridPosition(r, c, tx)

            for c in range(self._half_cols):
                x = (c - half_center_col) * self._pitch + half_offset
                yield GridPosition(r, c + 6, Transform.translate(x, row_y))


class SplitBGADecorated(SilkscreenOutline, Pad1Marker, ExcessCourtyard, SplitBGABase):
    """Split BGA with decorations"""

    def __base_init__(self) -> None:
        super().__base_init__()


class DDR4NumberingScheme(AlphaDictNumbering):
    """Custom numbering scheme for DDR4 split BGA.

    Maps grid columns 0-2 to pad columns 1-3, and grid columns 6-8 to pad columns 7-9.
    """

    def col_name(self, col: int) -> str:
        return str(col + 1)


class FBGA96(A1, DDR4NumberingScheme, SplitBGADecorated):
    """FBGA96 split BGA landpattern.

    96 balls: 16 rows x 9 columns in two 3-column halves.

    - Pitch: 0.80mm, Ball diameter: 0.42mm
    - Gap between halves: 3.2mm
    - Package body: 7.50mm x 13.0mm x 1.1mm
    - Density level C
    """

    def __init__(self) -> None:
        super().__init__(
            num_rows=16,
            half_cols=3,
            ball_diameter=0.42,
            pitch=0.80,
            gap=3.20,
        )
        self.pad_config(SMDPadConfig(copper=0.05))
        self.package_body(
            RectanglePackage(
                width=Toleranced(7.50, 0.0),
                length=Toleranced(13.0, 0.0),
                height=Toleranced(1.1, 0.0),
            )
        )
        self.density_level(DensityLevel.C)


class MT40A1G16TB_062E_F(Component):
    """Micron MT40A1G16TB-062E:F DDR4 SDRAM, x16, FBGA96.

    The DDR4 signals are the ``ddr4`` bundle: an x16, single-rank
    :py:class:`~jitxexamples.protocols.memory.ddr4.DDR4` with one CK pair, one
    bank-group bit and two bank-address bits.

    - ``ddr4.data.DQ[0]`` to ``[7]`` are DQL0 to DQL7, ``[8]`` to ``[15]`` are
      DQU0 to DQU7.
    - ``ddr4.data.DQS[0]`` and ``DM_n[0]`` are the lower byte's strobe and
      mask, ``DQS[1]`` and ``DM_n[1]`` the upper byte's.
    - ``ddr4.acc`` holds CK, CKE, A0 to A16, ACT_n, BG0, BA0 and BA1, CS_n,
      RESET_n, ODT, PAR and ALERT_n.

    The other pins are ports of their own: TEN, NC, VDD, VSS, VDDQ, VSSQ, VPP,
    VREFCA and ZQ.
    """

    reference_designator_prefix = "U"
    mpn = "MT40A1G16TB-062E:F"
    manufacturer = "Micron"

    ddr4 = DDR4(DDR4Width.x16, DDR4Rank.SingleRank, ck_count=1, bg_count=1)
    "DDR4 interface"

    TEN = Port()
    NC = Port()
    VDD = [Port() for _ in range(10)]
    VSS = [Port() for _ in range(9)]
    VDDQ = [Port() for _ in range(10)]
    VSSQ = [Port() for _ in range(10)]
    VPP = [Port() for _ in range(2)]
    VREFCA = Port()
    ZQ = Port()

    landpattern = FBGA96()
    symbol = BoxSymbol()

    mapping = [
        PadMapping(
            {
                ddr4.data.DQ[0]: landpattern.G[2],
                ddr4.data.DQ[1]: landpattern.F[7],
                ddr4.data.DQ[2]: landpattern.H[3],
                ddr4.data.DQ[3]: landpattern.H[7],
                ddr4.data.DQ[4]: landpattern.H[2],
                ddr4.data.DQ[5]: landpattern.H[8],
                ddr4.data.DQ[6]: landpattern.J[3],
                ddr4.data.DQ[7]: landpattern.J[7],
                ddr4.data.DQ[8]: landpattern.A[3],
                ddr4.data.DQ[9]: landpattern.B[8],
                ddr4.data.DQ[10]: landpattern.C[3],
                ddr4.data.DQ[11]: landpattern.C[7],
                ddr4.data.DQ[12]: landpattern.C[2],
                ddr4.data.DQ[13]: landpattern.C[8],
                ddr4.data.DQ[14]: landpattern.D[3],
                ddr4.data.DQ[15]: landpattern.D[7],
                ddr4.acc.A[0]: landpattern.P[3],
                ddr4.acc.A[1]: landpattern.P[7],
                ddr4.acc.A[2]: landpattern.R[3],
                ddr4.acc.A[3]: landpattern.N[7],
                ddr4.acc.A[4]: landpattern.N[3],
                ddr4.acc.A[5]: landpattern.P[8],
                ddr4.acc.A[6]: landpattern.P[2],
                ddr4.acc.A[7]: landpattern.R[8],
                ddr4.acc.A[8]: landpattern.R[2],
                ddr4.acc.A[9]: landpattern.R[7],
                ddr4.acc.A[10]: landpattern.M[3],
                ddr4.acc.A[11]: landpattern.T[2],
                ddr4.acc.A[12]: landpattern.M[7],
                ddr4.acc.A[13]: landpattern.T[8],
                ddr4.acc.A[14]: landpattern.L[2],
                ddr4.acc.A[15]: landpattern.M[8],
                ddr4.acc.A[16]: landpattern.L[8],
                ddr4.acc.BA[0]: landpattern.N[2],
                ddr4.acc.BA[1]: landpattern.N[8],
                ddr4.acc.BG[0]: landpattern.M[2],
                ddr4.acc.CK[0].p: landpattern.K[7],
                ddr4.acc.CK[0].n: landpattern.K[8],
                ddr4.acc.CKE[0]: landpattern.K[2],
                ddr4.acc.CS_n[0]: landpattern.L[7],
                ddr4.acc.ODT[0]: landpattern.K[3],
                ddr4.acc.ACT_n: landpattern.L[3],
                ddr4.acc.RESET_n: landpattern.P[1],
                ddr4.acc.PAR: landpattern.T[3],
                TEN: landpattern.N[9],
                ddr4.acc.ALERT_n: landpattern.P[9],
                NC: landpattern.T[7],
                ddr4.data.DQS[1].p: landpattern.B[7],
                ddr4.data.DQS[1].n: landpattern.A[7],
                ddr4.data.DQS[0].p: landpattern.G[3],
                ddr4.data.DQS[0].n: landpattern.F[3],
                ddr4.data.DM_n[1]: landpattern.E[2],
                ddr4.data.DM_n[0]: landpattern.E[7],
                VDD[0]: landpattern.B[3],
                VDD[1]: landpattern.B[9],
                VDD[2]: landpattern.D[1],
                VDD[3]: landpattern.G[7],
                VDD[4]: landpattern.J[1],
                VDD[5]: landpattern.J[9],
                VDD[6]: landpattern.L[1],
                VDD[7]: landpattern.L[9],
                VDD[8]: landpattern.R[1],
                VDD[9]: landpattern.T[9],
                VSS[0]: landpattern.B[2],
                VSS[1]: landpattern.E[1],
                VSS[2]: landpattern.E[9],
                VSS[3]: landpattern.G[8],
                VSS[4]: landpattern.K[1],
                VSS[5]: landpattern.K[9],
                VSS[6]: landpattern.M[9],
                VSS[7]: landpattern.N[1],
                VSS[8]: landpattern.T[1],
                VDDQ[0]: landpattern.A[1],
                VDDQ[1]: landpattern.A[9],
                VDDQ[2]: landpattern.C[1],
                VDDQ[3]: landpattern.D[9],
                VDDQ[4]: landpattern.F[2],
                VDDQ[5]: landpattern.F[8],
                VDDQ[6]: landpattern.G[1],
                VDDQ[7]: landpattern.G[9],
                VDDQ[8]: landpattern.J[2],
                VDDQ[9]: landpattern.J[8],
                VSSQ[0]: landpattern.A[2],
                VSSQ[1]: landpattern.A[8],
                VSSQ[2]: landpattern.C[9],
                VSSQ[3]: landpattern.D[2],
                VSSQ[4]: landpattern.D[8],
                VSSQ[5]: landpattern.E[3],
                VSSQ[6]: landpattern.E[8],
                VSSQ[7]: landpattern.F[1],
                VSSQ[8]: landpattern.H[1],
                VSSQ[9]: landpattern.H[9],
                VPP[0]: landpattern.B[1],
                VPP[1]: landpattern.R[9],
                VREFCA: landpattern.M[1],
                ZQ: landpattern.F[9],
            }
        )
    ]
