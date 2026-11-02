"""JS4 shipping design: the VP1002 driving a Micron MT53E1G32D2FW LPDDR4X.

The FPGA offers every byte swap and bit swap AMD's rules allow on one
layout, the single channel x32 pinout, flipped, on banks 702 and 701
(:py:mod:`.fpga`), with each position where AMD's VMK180, VCK190 and VPK120
boards put it, CS1 aside on the single rank VCK190 (:py:mod:`.pinout`). The design requires one interface, nets it
to the memory with plain nets, and applies the UG863 timing constraints
(:py:mod:`.constraint`). JITX picks the assignment when the board is routed.
The design has no routes, so its issue report shows each constrained path
unassigned, or for CKE without a path; :py:mod:`.proof` routes part of it in
code to show the constraints bind. Vivado validation of the chosen
assignment is the designer's step: the kit exports no XDC.

Board and substrate are JS1's 20-layer HDI stackup on its 80 x 80 mm board.

To see the report, save this as a script in the project root and run it
with the project's runtime running::

    import jitx

    from jitxexamples.jumpstart_kits.js4_fpga_lpddr4x.main import JS4Design


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(JS4Design).issues(satisfied=True, wait=30)
            if not report.complete:
                print("report incomplete: raise wait and run again")
            for group in report.groups():
                print("met" if group.satisfied else "NOT MET", group.text)
                if len(group.issues) > 1:
                    for issue in group:
                        print("   ", issue.text)


    if __name__ == "__main__":
        main()

``main()`` sits behind the ``__name__`` guard because JITX design discovery
imports every ``.py`` file under the project root.

Not modeled yet: the system
clock source, memory power rails and decoupling, CKE termination, the
RESET_n pull-down, ZQ and ODT resistors, and the IO_VR_700 resistor.
"""

from jitx.circuit import Circuit
from jitx.design import Design
from jitx.si import ReferencePlanes

from jitxexamples.components.memories.MT53E1G32D2FW_046_WT_B import (
    MT53E1G32D2FW_046_WT_B,
)

from jitxexamples.protocols.memory.lpddr4 import LPDDR4Constraint

from ..js1_stackup_components.hdi_stackup.board import HDIBoard, HDISubstrate
from .bundles import VersalLPDDR4X
from .constraint import UG863_PARAMS
from .fpga import VP1002LPDDR4X


class JS4Circuit(Circuit):
    """The FPGA, the memory, the nets between them and the constraints.

    The memory sits below bank 702, turned 180 degrees so its channel B
    balls face the FPGA.
    """

    def __init__(self) -> None:
        self.fpga = VP1002LPDDR4X()
        self.fpga.fpga.at(0, 12)
        self.memory = MT53E1G32D2FW_046_WT_B().at(10, -14.5, rotate=180)
        bus = self.fpga.require(VersalLPDDR4X)
        mem = self.memory.lpddr4

        # One field per LPDDR4X signal role. Byte-lane signals index the byte,
        # 0 to 3 across both channels (bytes 0 and 1 on channel A, 2 and 3 on
        # channel B), so DQ[2][5] is bit 5 of channel B's byte lane 0.
        # Per-channel signals index the channel, 0 for A and 1 for B, so
        # CA[1][3] is CA3 on channel B.
        channels = list(zip(bus.ch, mem.ch, strict=True))
        lanes = [(s, d) for sc, dc in channels for s, d in zip(sc.d, dc.d, strict=True)]
        self.RESET_n = bus.reset_n + self.memory.RESET_n
        self.DQ = [[a + b for a, b in zip(s.dq, d.dq, strict=True)] for s, d in lanes]
        self.DQS = [s.dqs + d.dqs for s, d in lanes]
        self.DMI = [s.dmi + d.dmi for s, d in lanes]
        self.CK = [s.ck + d.ck for s, d in channels]
        self.CKE = [s.cke + d.cke[0] + d.cke[1] for s, d in channels]
        self.CS = [
            [a + b for a, b in zip(s.cs, d.cs, strict=True)] for s, d in channels
        ]
        self.CA = [
            [a + b for a, b in zip(s.ca, d.ca, strict=True)] for s, d in channels
        ]

        # The memory's VSS joins the FPGA's main ground, which every HDI
        # routing structure references.
        self.gnd_net = self.fpga.pwr_vcco_700.Vn + self.memory.VSS
        with ReferencePlanes(self.gnd_net):
            self.lpddr4x_si = LPDDR4Constraint(
                diff_structure=HDISubstrate.DRS_100,
                se_structure=HDISubstrate.SE_50,
                params=UG863_PARAMS,
            )
            self.lpddr4x_si.constrain(bus, mem)


class JS4Design(Design):
    """The shipping design: no routes."""

    board = HDIBoard()
    substrate = HDISubstrate()
    circuit = JS4Circuit()
