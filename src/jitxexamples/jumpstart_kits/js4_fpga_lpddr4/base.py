"""JS4 base design: the VP1002 connected to a Micron LPDDR4 memory, ready
for layout.

The VP1002 offers its LPDDR4 pins with every swap AMD's rules allow
(:py:mod:`jitxexamples.jumpstart_kits.vp1002_lpddr4`); the design requires
one interface and nets it to a Micron MT53E1G32D2FW with plain nets. JITX
picks the pin assignment when the board is routed.

Board and substrate are the 18-layer reference stackup,
:py:mod:`jitxexamples.substrates.reference_18layer`, transcribed from a
production FPGA evaluation board's fabrication drawing, on an 80 x 80 mm
board.

The design also carries the supplies, straps, calibration resistors and
decoupling of :py:mod:`jitxexamples.jumpstart_kits.vp1002_lpddr4.power` and
:py:mod:`jitxexamples.jumpstart_kits.vp1002_lpddr4.decoupling`: each rail a
named net, the ZQ and IO_VR calibration resistors, each transceiver
calibration supply tied to its AVTT rail through its RREF resistor, and a
decoupling set on every supply rail of the memory (sized to TI's LPDDR4
layout guideline) and of the FPGA (a reference board's, trimmed), each
capacitor tied to a ball of its rail, by a ShortTrace below 10 uF and a
plain net for bulk (:py:mod:`~jitxexamples.jumpstart_kits.vp1002_lpddr4.decoupling`),
and its return pad on the ground the routing structures reference.

The interface runs as LPDDR4, so the VCCO of XPIO banks 700 to 702 and the
memory's VDD2 and VDDQ are one 1.1 V net (UG863 Table 23;
:py:mod:`jitxexamples.jumpstart_kits.vp1002_lpddr4.power`):
:py:class:`JS4BaseCircuit` joins the three VCCO rails to the memory's
``LP4_1V1``. The memory's VDD1, 1.8 V, is its own net. Bank 700 carries no
memory signal; its VCCO is on the 1.1 V net too, a design choice: the bank
must stay powered (it holds the DCI reference for every XPIO bank, UG863
"IO_VR_700, IO_VR_800 Pin Differences"), 1.1 V is inside its VCCO range
(DS959 Table 1), and a rail of its own would need a supply that nothing
else on the board needs.

Each resistor and capacitor sits in the circuit of the part it serves,
:py:class:`JS4Fpga` or :py:class:`JS4Memory`. Only the FPGA is placed: the
memory, the resistors and the capacitors are left for placement in the
layout. The design applies no constraints and no design rules;
:py:mod:`.part3_si_constraints` adds the SI constraints.

:py:class:`JS4BaseCircuit` builds the FPGA's circuit and the memory's
through ``new_fpga`` and ``new_memory``, so a layout can subclass them and
put each part's vias and routes in the part's own circuit, where they move
when that circuit moves.

The capacitors and the resistors are queries on the example parts
catalogue, so a project that builds the design needs a parts chain that
lists it, set up as the "Parts configuration" section of the repository
README says (https://github.com/JITx-Inc/jitx-examples#parts-configuration).
In short, copy the CSV out of the installed package, into a ``parts/``
directory that exists::

    import importlib.resources
    import shutil

    shutil.copy(
        importlib.resources.files("jitxexamples") / "parts" / "example-passives.csv",
        "parts/approved-parts.csv",
    )

and chain it without ``ideal``, in ``pyproject.toml``, so a query the
catalogue cannot meet fails instead of resolving to a part that ignores its
filters::

    [tool.jitx.parts]
    chain = ["csv:parts/approved-parts.csv"]

The copy is an example, not an approved list.

Not modeled yet: the system clock source, the regulators and their remote
sense on VCCINT_SENSE and GND_SENSE, CKE termination, the RESET_n pull-down,
the system monitor's two ferrite beads
(:py:mod:`jitxexamples.jumpstart_kits.vp1002_lpddr4.power`), and
decoupling counts for this device: AMD's Power Design Manager gives them
from a design's resource use, so the FPGA sets here are a reference
board's, trimmed
(:py:mod:`jitxexamples.jumpstart_kits.vp1002_lpddr4.decoupling`).
"""

from collections.abc import Mapping

from jitx.circuit import Circuit
from jitx.design import Design
from jitx.net import Net
from jitxlib.parts import Capacitor

from jitxexamples.components.memories.MT53E1G32D2FW_046_WT_B import (
    MT53E1G32D2FW_046_WT_B,
)
from jitxexamples.substrates.reference_18layer import (
    Reference18Board,
    Reference18Substrate,
)

from ..vp1002_lpddr4.bundles import VersalLPDDR4
from ..vp1002_lpddr4.circuit import VP1002LPDDR4
from ..vp1002_lpddr4.decoupling import (
    XPIO_BANKS,
    FpgaDecoupling,
    MemoryDecoupling,
    RailLayout,
    XpioBankDecoupling,
    ball_grid,
)
from ..vp1002_lpddr4.power import FpgaStraps, GtCalibration, MemoryStraps


class JS4Fpga(VP1002LPDDR4):
    """The VP1002, placed, with its straps, its calibration resistors and
    the decoupling of every supply rail, so each of those parts sits in the
    FPGA's circuit."""

    def __init__(self) -> None:
        super().__init__()
        ic = self.fpga
        ic.at(0, 12)
        grid = ball_grid(ic)
        layouts = self.decoupling_layouts()
        self.vcco_decoupling = [
            XpioBankDecoupling(balls, grid, layouts.get(bank))
            for bank, balls in zip(
                XPIO_BANKS, (ic.VCCO_700, ic.VCCO_701, ic.VCCO_702), strict=True
            )
        ]
        self.decoupling = FpgaDecoupling(self, grid, layouts)
        self.straps = FpgaStraps(self)
        self.gt_cal = GtCalibration(self)
        # VCCAUX_SMON's capacitors return to GND_SMON (AM006 v1.5 Figure 1).
        self.smon_return = Net(
            [
                self.pwr_vccaux_smon.Vn,
                *(c.p2 for c in self.decoupling.smon_capacitors()),
            ]
        )

    def decoupling_layouts(self) -> Mapping[str, RailLayout]:
        """How a layout treats some capacitors of the FPGA's sets, by rail
        name (:py:class:`~..vp1002_lpddr4.decoupling.RailLayout`), read
        before any capacitor is created. Here none: every capacitor of every
        set, each one below 10 uF tied to its ball by a ShortTrace. A
        layout's subclass overrides this to leave capacitors out or tie them
        by a plain net."""
        return {}

    def ground_capacitors(self) -> list[Capacitor]:
        """Every capacitor that returns to the main ground: the XPIO banks'
        and every other rail's but VCCAUX_SMON's."""
        return [
            *(c for bank in self.vcco_decoupling for c in bank.capacitors()),
            *self.decoupling.capacitors(),
        ]


class JS4Memory(Circuit):
    """The Micron memory with its rails' straps, its ZQ resistors and its
    decoupling, so each of those parts sits in the memory's circuit. Nothing
    is placed."""

    def __init__(self) -> None:
        self.memory = MT53E1G32D2FW_046_WT_B()
        self.decoupling = MemoryDecoupling(self.memory)
        self.straps = MemoryStraps(self.memory)


class JS4BaseCircuit(Circuit):
    """The FPGA and the memory, each in its own circuit with its straps,
    calibration resistors and decoupling, and the nets between them. Only
    the FPGA is placed; no constraints, no design rules."""

    def __init__(self) -> None:
        self.fpga = self.new_fpga()
        self.memory = self.new_memory()
        bus = self.fpga.require(VersalLPDDR4)
        # JITX names a required interface after the first net it is found in,
        # and the constraint paths that start on it after that: this net
        # comes first so the paths read lpddr4.ch[0].ca[0], not as members
        # of whichever signal's net came first.
        self.lpddr4 = Net([bus])
        memory = self.memory.memory
        mem = memory.lpddr4

        # One field per LPDDR4 signal role. Byte-lane signals index the byte,
        # 0 to 3 across both channels (bytes 0 and 1 on channel A, 2 and 3 on
        # channel B), so DQ[2][5] is bit 5 of channel B's byte lane 0.
        # Per-channel signals index the channel, 0 for A and 1 for B, so
        # CA[1][3] is CA3 on channel B.
        channels = list(zip(bus.ch, mem.ch, strict=True))
        lanes = [(s, d) for sc, dc in channels for s, d in zip(sc.d, dc.d, strict=True)]
        self.RESET_n = bus.reset_n + memory.RESET_n
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

        # The VCCO of XPIO banks 700 to 702 joins the memory's 1.1 V net of
        # VDD2 and VDDQ: one rail.
        self.LP4_1V1 = Net(
            [
                self.fpga.pwr_vcco_700.Vp,
                self.fpga.pwr_vcco_701.Vp,
                self.fpga.pwr_vcco_702.Vp,
                memory.VDD2[0],
            ]
        )

        # The memory's VSS and every capacitor's return pad join the FPGA's
        # main ground, which every routing structure of the reference
        # substrate references.
        self.gnd_net = Net(
            [
                self.fpga.pwr_vcco_700.Vn,
                *memory.VSS,
                *(c.p2 for c in self.memory.decoupling.capacitors()),
                *(c.p2 for c in self.fpga.ground_capacitors()),
            ]
        )

    def new_fpga(self) -> JS4Fpga:
        """The FPGA's circuit."""
        return JS4Fpga()

    def new_memory(self) -> JS4Memory:
        """The memory's circuit."""
        return JS4Memory()

    def lpddr4_bus(self) -> VersalLPDDR4:
        """The LPDDR4 interface required from the FPGA, read back from
        :py:attr:`lpddr4`, the net that holds it."""
        found = [p for p in self.lpddr4 if isinstance(p, VersalLPDDR4)]
        if len(found) != 1:
            raise ValueError(f"expected one required interface, found {len(found)}")
        return found[0]


class JS4BaseDesign(Design):
    """The base design: connected, no routes, only the FPGA placed."""

    board = Reference18Board()
    substrate = Reference18Substrate()
    circuit = JS4BaseCircuit()
