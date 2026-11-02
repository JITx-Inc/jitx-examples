"""Micron MT53E1G32D2FW-046 WT:B LPDDR4X/LPDDR4 SDRAM.

32 Gb (4 GB), 1 Gig x 32: two dies, two x16 channels (A and B), dual rank,
in a 200-ball TFBGA, 10 mm x 14.5 mm x 1.1 mm (package code FW).

Source: Micron, *LPDDR4X/LPDDR4 SDRAM* data sheet
(``z42m_embedded_lpddr4x_lpddr4.pdf``, Rev. I, 04/2023),
https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8606/z42m-embedded-lpddr4x-lpddr4.pdf.
Checked against it:

- Part number, density and organization: Figure 1 (part number chart) and
  Table 2 (part number list).
- Ball map: Figure 6, "200-Ball Dual-Channel, Dual-Rank Discrete FBGA". Every
  one of the 200 balls is mapped here, including the 12 DNU and 5 NC balls.
- Grid and body: Figure 10, "200-Ball TFBGA - 10mm x 14.5mm x 1.1mm (Package
  Code: FW)": 22 rows at 0.65 mm pitch, 12 columns at 0.8 mm pitch, body
  10 +/-0.1 mm by 14.5 +/-0.1 mm, height 1 +/-0.1 mm. Columns 6 and 7 and
  rows L and M carry no balls.

The data sheet gives the package's ball pads (0.40 mm SMD) but no PCB land
size. The land here is 0.40 mm to match them; check it against your
fabricator's BGA rules.
"""

from jitx import PadMapping
from jitx.component import Component
from jitx.landpattern import Pad
from jitx.net import Port
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.grid_layout import GridPosition
from jitxlib.landpatterns.grid_planner import GridPlanner
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from jitxexamples.protocols.memory.lpddr4 import LPDDR4, LPDDR4Rank, LPDDR4Width


class FW200Depopulation(GridPlanner):
    """No balls in columns 6 and 7 or rows L and M of the 22 x 12 grid."""

    def is_active(self, pos: GridPosition, num_rows: int, num_cols: int) -> bool | None:
        if pos.column in (5, 6) or pos.row in (10, 11):
            return False
        return None


class FW200Landpattern(BGA):
    """200-ball TFBGA, package code FW: 12 columns at 0.8 mm, 22 rows at
    0.65 mm, columns 6 and 7 and rows L and M empty."""

    AA: dict[int, Pad]
    AB: dict[int, Pad]

    def __init__(self) -> None:
        super().__init__(
            num_rows=22, num_cols=12, ball_diameter=0.40, pitch=(0.8, 0.65)
        )
        self.pad_config(SMDPadConfig())
        self.grid_planner(FW200Depopulation())
        self.package_body(
            RectanglePackage(
                width=Toleranced(10.0, 0.1),
                length=Toleranced(14.5, 0.1),
                height=Toleranced(1.0, 0.1),
            )
        )


class MT53E1G32D2FW_046_WT_B(Component):
    """Micron MT53E1G32D2FW-046 WT:B, 32 Gb LPDDR4X/LPDDR4, x32, dual rank.

    The LPDDR4 signals are the leaves of the :py:attr:`lpddr4` bundle; the
    other balls keep their data sheet names, with one port per supply or
    ground name.
    """

    reference_designator_prefix = "U"
    mpn = "MT53E1G32D2FW-046 WT:B"
    manufacturer = "Micron"

    lpddr4 = LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank2)
    """LPDDR4 interface. ``ch[0]`` is channel A and ``ch[1]`` channel B; in
    each channel byte lane ``d[0]`` is DQ0 to DQ7 and ``d[1]`` DQ8 to DQ15.
    ``ck.p``/``ck.n`` are CK_t/CK_c and ``dqs.p``/``dqs.n`` are DQS_t/DQS_c."""

    ODT_CA_A = Port()
    ODT_CA_B = Port()
    RESET_n = Port()
    ZQ0 = Port()
    ZQ1 = Port()
    VDD1 = Port()
    VDD2 = Port()
    VDDQ = Port()
    VSS = Port()
    NC = Port()
    "No connect (5 balls)"
    DNU = Port()
    "Do not use (12 corner balls)"

    landpattern = FW200Landpattern()
    symbol = BoxSymbol()

    mapping = [
        PadMapping(
            {
                lpddr4.ch[0].d[0].dq[0]: landpattern.B[2],  # DQ0_A
                lpddr4.ch[0].d[0].dq[7]: landpattern.B[4],  # DQ7_A
                lpddr4.ch[0].d[1].dq[7]: landpattern.B[9],  # DQ15_A
                lpddr4.ch[0].d[1].dq[0]: landpattern.B[11],  # DQ8_A
                lpddr4.ch[0].d[0].dq[1]: landpattern.C[2],  # DQ1_A
                lpddr4.ch[0].d[0].dmi: landpattern.C[3],  # DMI0_A
                lpddr4.ch[0].d[0].dq[6]: landpattern.C[4],  # DQ6_A
                lpddr4.ch[0].d[1].dq[6]: landpattern.C[9],  # DQ14_A
                lpddr4.ch[0].d[1].dmi: landpattern.C[10],  # DMI1_A
                lpddr4.ch[0].d[1].dq[1]: landpattern.C[11],  # DQ9_A
                lpddr4.ch[0].d[0].dqs.p: landpattern.D[3],  # DQS0_t_A
                lpddr4.ch[0].d[1].dqs.p: landpattern.D[10],  # DQS1_t_A
                lpddr4.ch[0].d[0].dq[2]: landpattern.E[2],  # DQ2_A
                lpddr4.ch[0].d[0].dqs.n: landpattern.E[3],  # DQS0_c_A
                lpddr4.ch[0].d[0].dq[5]: landpattern.E[4],  # DQ5_A
                lpddr4.ch[0].d[1].dq[5]: landpattern.E[9],  # DQ13_A
                lpddr4.ch[0].d[1].dqs.n: landpattern.E[10],  # DQS1_c_A
                lpddr4.ch[0].d[1].dq[2]: landpattern.E[11],  # DQ10_A
                lpddr4.ch[0].d[0].dq[3]: landpattern.F[2],  # DQ3_A
                lpddr4.ch[0].d[0].dq[4]: landpattern.F[4],  # DQ4_A
                lpddr4.ch[0].d[1].dq[4]: landpattern.F[9],  # DQ12_A
                lpddr4.ch[0].d[1].dq[3]: landpattern.F[11],  # DQ11_A
                lpddr4.ch[0].ca[0]: landpattern.H[2],  # CA0_A
                lpddr4.ch[0].cs[1]: landpattern.H[3],  # CS1_A
                lpddr4.ch[0].cs[0]: landpattern.H[4],  # CS0_A
                lpddr4.ch[0].ca[2]: landpattern.H[9],  # CA2_A
                lpddr4.ch[0].ca[3]: landpattern.H[10],  # CA3_A
                lpddr4.ch[0].ca[4]: landpattern.H[11],  # CA4_A
                lpddr4.ch[0].ca[1]: landpattern.J[2],  # CA1_A
                lpddr4.ch[0].cke[0]: landpattern.J[4],  # CKE0_A
                lpddr4.ch[0].cke[1]: landpattern.J[5],  # CKE1_A
                lpddr4.ch[0].ck.p: landpattern.J[8],  # CK_t_A
                lpddr4.ch[0].ck.n: landpattern.J[9],  # CK_c_A
                lpddr4.ch[0].ca[5]: landpattern.J[11],  # CA5_A
                lpddr4.ch[1].ca[1]: landpattern.P[2],  # CA1_B
                lpddr4.ch[1].cke[0]: landpattern.P[4],  # CKE0_B
                lpddr4.ch[1].cke[1]: landpattern.P[5],  # CKE1_B
                lpddr4.ch[1].ck.p: landpattern.P[8],  # CK_t_B
                lpddr4.ch[1].ck.n: landpattern.P[9],  # CK_c_B
                lpddr4.ch[1].ca[5]: landpattern.P[11],  # CA5_B
                lpddr4.ch[1].ca[0]: landpattern.R[2],  # CA0_B
                lpddr4.ch[1].cs[1]: landpattern.R[3],  # CS1_B
                lpddr4.ch[1].cs[0]: landpattern.R[4],  # CS0_B
                lpddr4.ch[1].ca[2]: landpattern.R[9],  # CA2_B
                lpddr4.ch[1].ca[3]: landpattern.R[10],  # CA3_B
                lpddr4.ch[1].ca[4]: landpattern.R[11],  # CA4_B
                lpddr4.ch[1].d[0].dq[3]: landpattern.U[2],  # DQ3_B
                lpddr4.ch[1].d[0].dq[4]: landpattern.U[4],  # DQ4_B
                lpddr4.ch[1].d[1].dq[4]: landpattern.U[9],  # DQ12_B
                lpddr4.ch[1].d[1].dq[3]: landpattern.U[11],  # DQ11_B
                lpddr4.ch[1].d[0].dq[2]: landpattern.V[2],  # DQ2_B
                lpddr4.ch[1].d[0].dqs.n: landpattern.V[3],  # DQS0_c_B
                lpddr4.ch[1].d[0].dq[5]: landpattern.V[4],  # DQ5_B
                lpddr4.ch[1].d[1].dq[5]: landpattern.V[9],  # DQ13_B
                lpddr4.ch[1].d[1].dqs.n: landpattern.V[10],  # DQS1_c_B
                lpddr4.ch[1].d[1].dq[2]: landpattern.V[11],  # DQ10_B
                lpddr4.ch[1].d[0].dqs.p: landpattern.W[3],  # DQS0_t_B
                lpddr4.ch[1].d[1].dqs.p: landpattern.W[10],  # DQS1_t_B
                lpddr4.ch[1].d[0].dq[1]: landpattern.Y[2],  # DQ1_B
                lpddr4.ch[1].d[0].dmi: landpattern.Y[3],  # DMI0_B
                lpddr4.ch[1].d[0].dq[6]: landpattern.Y[4],  # DQ6_B
                lpddr4.ch[1].d[1].dq[6]: landpattern.Y[9],  # DQ14_B
                lpddr4.ch[1].d[1].dmi: landpattern.Y[10],  # DMI1_B
                lpddr4.ch[1].d[1].dq[1]: landpattern.Y[11],  # DQ9_B
                lpddr4.ch[1].d[0].dq[0]: landpattern.AA[2],  # DQ0_B
                lpddr4.ch[1].d[0].dq[7]: landpattern.AA[4],  # DQ7_B
                lpddr4.ch[1].d[1].dq[7]: landpattern.AA[9],  # DQ15_B
                lpddr4.ch[1].d[1].dq[0]: landpattern.AA[11],  # DQ8_B
                DNU: [
                    landpattern.A[1],
                    landpattern.A[2],
                    landpattern.A[11],
                    landpattern.A[12],
                    landpattern.B[1],
                    landpattern.B[12],
                    landpattern.AA[1],
                    landpattern.AA[12],
                    landpattern.AB[1],
                    landpattern.AB[2],
                    landpattern.AB[11],
                    landpattern.AB[12],
                ],
                VSS: [
                    landpattern.A[3],
                    landpattern.A[10],
                    landpattern.C[1],
                    landpattern.C[5],
                    landpattern.C[8],
                    landpattern.C[12],
                    landpattern.D[2],
                    landpattern.D[4],
                    landpattern.D[9],
                    landpattern.D[11],
                    landpattern.E[1],
                    landpattern.E[5],
                    landpattern.E[8],
                    landpattern.E[12],
                    landpattern.G[1],
                    landpattern.G[3],
                    landpattern.G[5],
                    landpattern.G[8],
                    landpattern.G[10],
                    landpattern.G[12],
                    landpattern.J[1],
                    landpattern.J[3],
                    landpattern.J[10],
                    landpattern.J[12],
                    landpattern.K[2],
                    landpattern.K[4],
                    landpattern.K[9],
                    landpattern.K[11],
                    landpattern.N[2],
                    landpattern.N[4],
                    landpattern.N[9],
                    landpattern.N[11],
                    landpattern.P[1],
                    landpattern.P[3],
                    landpattern.P[10],
                    landpattern.P[12],
                    landpattern.T[1],
                    landpattern.T[3],
                    landpattern.T[5],
                    landpattern.T[8],
                    landpattern.T[10],
                    landpattern.T[12],
                    landpattern.V[1],
                    landpattern.V[5],
                    landpattern.V[8],
                    landpattern.V[12],
                    landpattern.W[2],
                    landpattern.W[4],
                    landpattern.W[9],
                    landpattern.W[11],
                    landpattern.Y[1],
                    landpattern.Y[5],
                    landpattern.Y[8],
                    landpattern.Y[12],
                    landpattern.AB[3],
                    landpattern.AB[5],
                    landpattern.AB[8],
                    landpattern.AB[10],
                ],
                VDD2: [
                    landpattern.A[4],
                    landpattern.A[9],
                    landpattern.F[5],
                    landpattern.F[8],
                    landpattern.H[1],
                    landpattern.H[5],
                    landpattern.H[8],
                    landpattern.H[12],
                    landpattern.K[1],
                    landpattern.K[3],
                    landpattern.K[10],
                    landpattern.K[12],
                    landpattern.N[1],
                    landpattern.N[3],
                    landpattern.N[10],
                    landpattern.N[12],
                    landpattern.R[1],
                    landpattern.R[5],
                    landpattern.R[8],
                    landpattern.R[12],
                    landpattern.U[5],
                    landpattern.U[8],
                    landpattern.AB[4],
                    landpattern.AB[9],
                ],
                ZQ0: landpattern.A[5],
                ZQ1: landpattern.A[8],
                VDDQ: [
                    landpattern.B[3],
                    landpattern.B[5],
                    landpattern.B[8],
                    landpattern.B[10],
                    landpattern.D[1],
                    landpattern.D[5],
                    landpattern.D[8],
                    landpattern.D[12],
                    landpattern.F[3],
                    landpattern.F[10],
                    landpattern.U[3],
                    landpattern.U[10],
                    landpattern.W[1],
                    landpattern.W[5],
                    landpattern.W[8],
                    landpattern.W[12],
                    landpattern.AA[3],
                    landpattern.AA[5],
                    landpattern.AA[8],
                    landpattern.AA[10],
                ],
                VDD1: [
                    landpattern.F[1],
                    landpattern.F[12],
                    landpattern.G[4],
                    landpattern.G[9],
                    landpattern.T[4],
                    landpattern.T[9],
                    landpattern.U[1],
                    landpattern.U[12],
                ],
                ODT_CA_A: landpattern.G[2],
                NC: [
                    landpattern.G[11],
                    landpattern.K[5],
                    landpattern.K[8],
                    landpattern.N[5],
                    landpattern.N[8],
                ],
                ODT_CA_B: landpattern.T[2],
                RESET_n: landpattern.T[11],
            }
        )
    ]
