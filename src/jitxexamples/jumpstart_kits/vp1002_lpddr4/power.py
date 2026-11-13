"""Supply rails, straps and calibration resistors for the VP1002 and a Micron
MT53E1G32D2FW LPDDR4 memory.

:py:class:`MemoryStraps` names the memory's two rails, VDD1 and the 1.1 V
net that joins VDD2 and VDDQ, ties its ODT_CA pins and holds its two ZQ
resistors. :py:class:`FpgaStraps` makes the ties the cited documents require
of the FPGA (its paired supplies, its unused battery, eFUSE and
system-monitor pins) and holds its DCI reference resistor.
:py:class:`GtCalibration` ties each transceiver calibration supply
to its AVTT rail and holds the transceivers' RREF resistors. Each sits in
the circuit of the part it serves, so each rail is a net a regulator can
join. Rail voltages are left to the
regulator; the maxima here are the ones the decoupling ratings need.

The interface runs as LPDDR4, so the memory's VDD2 and VDDQ and the VCCO of
XPIO banks 700 to 702 all run at 1.1 V (UG863 Table 23) and share one net,
:py:attr:`MemoryStraps.LP4_1V1`, which the base design joins to the three
VCCO rails. UG863 separates the SoC's VCCO 1.1 V supply from the
memory's VDDQ only when the memory must power down while the SoC stays
powered, which this design does not do. VDD1, 1.8 V, keeps its own net.

Sources
-------

- Micron, *LPDDR4X/LPDDR4 SDRAM* data sheet,
  ``z42m_embedded_lpddr4x_lpddr4.pdf``, Rev. I, 04/2023, the copy the memory
  component cites: Table 5 "Ball/Pad Descriptions for x32", "ZQ External
  Resistor, Tolerance, and Capacitive Loading" (page 196), Figure 3
  "Dual-Die, Dual-Channel Package Block Diagram", and Table 241
  "Recommended DC Operating Conditions" in "LPDDR4 1.10V VDDQ", the
  LPDDR4 rows.
- AMD UG863, *Versal Adaptive SoC PCB Design User Guide*, v1.12, 2026-06-16,
  https://docs.amd.com/r/en-US/ug863-versal-pcb-design: "Signals and
  Connections for LPDDR4/4x Interfaces", Table 22 "LPDDR4/4x Signal
  Definitions" and Table 23 "Typical Supply Voltages for LPDDR4 and LPDDR4x",
  with its note on separating the SoC's VCCO from VDDQ; "IO_VR_700,
  IO_VR_800 Pin Differences".
- AMD AM010, *Versal Adaptive SoC SelectIO Resources Architecture Manual*,
  v1.7, 2025-05-22, https://docs.amd.com/r/en-US/am010-versal-selectio:
  "Calibrated Termination (Digitally Controlled Impedance)".
- AMD DS959, *Versal Premium Series Data Sheet: DC and AC Switching
  Characteristics*, v1.8, 2026-02-06,
  https://docs.amd.com/r/en-US/ds959-versal-premium: Table 1 "Recommended
  Operating Conditions": the supply rows, and notes 4, 5, 6 and 8.
- AMD AM006, *Versal Adaptive SoC System Monitor Architecture Manual*, v1.5,
  2025-06-03, https://docs.amd.com/r/en-US/am006-versal-sysmon: Table 1
  "SYSMON Package Pins" in "SYSMON Dedicated Pinout Requirements", and Figure
  1 "SYSMON Pinout Requirements" in "Analog Power Supply and Ground".
- AMD AM002, *Versal Adaptive SoC GTY and GTYP Transceivers Architecture
  Manual*, https://docs.amd.com/go/en-US/am002-versal-gty-transceivers, and
  AMD AM017, *Versal Adaptive SoC GTM Transceivers Architecture Manual*,
  https://docs.amd.com/go/en-US/am017-versal-gtm-transceivers: in each,
  "Termination Resistor Calibration Circuit": the AVTTRCAL pin to the AVTT
  supply and to one pin of a 100 ohm precision resistor, the other pin to
  RREF, the two traces of the same length and geometry, under 0.5 ohm DC.
- Trenz Electronic TE0950 schematic SCH-TE0950-03-MAKE21C, rev 03,
  2023-12-19,
  https://shop.trenz-electronic.de/trenzdownloads/Trenz_Electronic/Development_Boards/TE0950/REV03/Documents/SCH-TE0950-03-MAKE21C.PDF,
  an XCVM1102 board, page 12 "V_GTY": GTYP_AVTTRCAL_R (ball P6) on the
  GTYP_AVTT node, and R41, 100R 1%, from that node to GTYP_RREF_R (ball
  P7).

Not modeled: the system clock source, the RESET_n pull-down and CKE
termination (UG863 Table 22: for LPDDR4, 160 ohm to GND and 160 ohm to
VDD2), the rail voltages of the FPGA's
supplies, which depend on the speed grade (DS959 Table 1), the regulators'
remote sense on VCCINT_SENSE and GND_SENSE, and AM006's two ferrite beads:
the example catalogue has none, so VCCAUX_SMON joins VCCAUX_PMC and
GND_SMON joins GND directly.
"""

from jitx import Net
from jitx.container import Container
from jitxlib.parts import AtMost, Resistor

from jitxexamples.components.memories.MT53E1G32D2FW_046_WT_B import (
    MT53E1G32D2FW_046_WT_B,
)

from .circuit import VP1002LPDDR4

VDD1_MAX = 1.95
"""Memory VDD1 maximum, V, LPDDR4. Micron Rev. I Table 241: 1.7, 1.8,
1.95 V."""

VDD2_MAX = 1.17
"""Memory VDD2 maximum, V, LPDDR4. Micron Rev. I Table 241: 1.06, 1.1,
1.17 V."""

VDDQ_MAX = 1.17
"""Memory VDDQ maximum, V, LPDDR4. Micron Rev. I Table 241: 1.06, 1.1,
1.17 V."""

VCCO_MAX = 1.575
"""XPIO VCCO maximum, V. DS959 v1.8 Table 1: 0.950 to 1.575 V. UG863 v1.12
Table 23 runs the controller's banks at 1.1 V for LPDDR4, on the memory's
1.1 V net. The banks' capacitors are rated for this range maximum,
not the memory's 1.17 V, a design choice: it is the stricter rating, and it
keeps the parts the banks had."""

CORE_MAX = 0.906
"""Maximum, V, of VCCINT, VCCINT_GT, VCC_IO, VCC_PMC, VCC_PSFP, VCC_PSLP,
VCC_RAM and VCC_SOC: DS959 v1.8 Table 1, the high (H) voltage row of each,
the highest of its rows."""

AUX_MAX = 1.545
"""Maximum, V, of VCCAUX, VCCAUX_PMC, VCCAUX_SMON and the GTY and GTM
AVCCAUX rails. DS959 v1.8 Table 1: 1.455, 1.500, 1.545 V."""

PSIO_VCCO_MAX = 3.400
"""PSIO bank 5## VCCO maximum, V. DS959 v1.8 Table 1: 1.710 to 3.400 V."""

GTY_AVCC_MAX = 0.906
"""GTY AVCC maximum, V. DS959 v1.8 Table 1: 0.854, 0.880, 0.906 V."""

GTM_AVCC_MAX = 0.948
"""GTM AVCC maximum, V. DS959 v1.8 Table 1, E or I temperature range: 0.892,
0.920, 0.948 V."""

GT_AVTT_MAX = 1.236
"""GTY and GTM AVTT maximum, V. DS959 v1.8 Table 1: 1.164, 1.200, 1.236 V."""

ZQ_RESISTANCE = 240.0
"""ZQ calibration resistor, ohms, ZQ ball to VDDQ. Micron Rev. I Table 5 (ZQ0,
ZQ1: "The ZQ pin shall be connected to VDDQ through a 240 ohm +/-1%
resistor") and page 196; UG863 v1.12 Table 22 (ZQ: 240 ohm to VDDQ)."""

ZQ_TOLERANCE = 0.01
"""ZQ resistor tolerance, +/-1%. Micron Rev. I page 196: "a 240 ohms, +/-1%
tolerance external resistor must be connected between the ZQ pin and VDDQ"."""

RREF_RESISTANCE = 100.0
"""Transceiver RREF resistor, ohms, from the AVTT rail to the RREF ball.
AM002 and AM017, "Termination Resistor Calibration Circuit": 100 ohm
precision; TE0950 rev 03 page 12, R41: 100R."""

RREF_TOLERANCE = 0.01
"TE0950 rev 03 page 12, R41: 1%."

IO_VR_RESISTANCE = 240.0
"""DCI reference resistor, ohms, IO_VR_700 to VCCO_700. UG863 v1.12
Table 22 (IO_VR_7xx: 240 ohm to VCCO_7xx); AM010 v1.7, "Calibrated
Termination": "Banks with IO_VR pins must have an external 240 ohm resistor
tied to the bank's VCCO", in every design. Neither gives a tolerance, so the
query pins none."""


class MemoryStraps(Container):
    """The memory's rails as named nets, VDD1 and the 1.1 V net of VDD2 and
    VDDQ, its ODT_CA straps and its two ZQ resistors.

    One ZQ resistor per ZQ ball. The dual-die part has one ZQ ball per die
    (Micron Rev. I Figure 3: ZQ0 on the die selected by CS0, ZQ1 on the die
    selected by CS1), and Table 5 ties each ZQ pin to VDDQ through its own
    240 ohm. Page 196 allows two ranks to share one resistor only if the
    controller keeps their ZQ calibrations from overlapping; separate
    resistors leave the controller free of that rule.
    """

    def __init__(self, memory: MT53E1G32D2FW_046_WT_B) -> None:
        self.r_zq = [
            Resistor(resistance=ZQ_RESISTANCE, tolerance=AtMost(ZQ_TOLERANCE)),
            Resistor(resistance=ZQ_RESISTANCE, tolerance=AtMost(ZQ_TOLERANCE)),
        ]
        self.LP4_VDD1 = Net(memory.VDD1, name="LP4_VDD1")
        # VDD2 and VDDQ on one 1.1 V net: UG863 v1.12 Table 23 and Micron
        # Rev. I Table 241 give both 1.1 V for LPDDR4. ODT_CA_A and ODT_CA_B
        # go straight to VDD2: UG863 v1.12 Table 22 ("Direct to VDD2", except
        # ODT_A on the pin-efficient 2x32 layout, not this x32 one). Micron
        # Rev. I Table 5: for LPDDR4 the pin turns CA on-die termination on
        # with the mode register, and is "bonded to VDD2" for the terminating
        # rank. Each ZQ resistor goes to VDDQ.
        self.LP4_1V1 = Net(
            [
                *memory.VDD2,
                *memory.VDDQ,
                memory.ODT_CA_A,
                memory.ODT_CA_B,
                *(r.p2 for r in self.r_zq),
            ],
            name="LP4_1V1",
        )
        self.ZQ = [
            Net([memory.ZQ0, self.r_zq[0].p1], name="LP4_ZQ0"),
            Net([memory.ZQ1, self.r_zq[1].p1], name="LP4_ZQ1"),
        ]


class FpgaStraps(Container):
    """The ties the vendors require of the FPGA's supplies and pins, and its
    DCI reference resistor.

    The FPGA's rails are already named nets with a ``Power`` port each on
    :py:class:`~.circuit.VP1002LPDDR4`; a regulator joins one at its
    ``Vp``.
    """

    def __init__(self, fpga: VP1002LPDDR4) -> None:
        # Bank 700 stays powered whatever its I/O: it holds the DCI reference
        # for every XPIO bank (UG863 v1.12, "IO_VR_700, IO_VR_800 Pin
        # Differences"; AM010 v1.7: "Banks with IO_VR pins must always be
        # powered by a valid VCCO level").
        self.r_io_vr = Resistor(resistance=IO_VR_RESISTANCE)
        self.IO_VR_700 = fpga.IO_VR_700 + self.r_io_vr.p1
        self.VCCO_700 = fpga.pwr_vcco_700.Vp + self.r_io_vr.p2
        # DS959 v1.8 Table 1 note 8: "VCC_IO must be connected to VCC_SOC".
        self.VCC_SOC = fpga.pwr_vcc_soc.Vp + fpga.pwr_vcc_io.Vp
        # DS959 v1.8 Table 1 note 4: "VCCAUX_SMON must be connected to
        # VCCAUX_PMC". AM006 v1.5 Figure 1 filters it through a ferrite bead;
        # the example catalogue has none, so the tie is direct.
        self.VCCAUX_PMC = fpga.pwr_vccaux_pmc.Vp + fpga.pwr_vccaux_smon.Vp
        # This design uses neither the battery-backed RAM and RTC nor eFUSE
        # programming. DS959 v1.8 Table 1 note 5: "When the battery-backed RAM
        # and the real-time clock are not used, connect to GND." Note 6:
        # "When not programming the eFUSEs, connect VCC_FUSE to GND." Each
        # rail's Vn is already on the main ground.
        self.VCC_BATT = fpga.pwr_vcc_batt.Vp + fpga.pwr_vcc_batt.Vn
        self.VCC_FUSE = fpga.pwr_vcc_fuse.Vp + fpga.pwr_vcc_fuse.Vn
        # System monitor, AM006 v1.5 Table 1, with the on-chip reference and
        # no external analog input: VP and VN "must be connected to GND_SMON
        # if not used", VREFP goes to GND_SMON with no external reference,
        # and VREFN "must always be connected to GND_SMON". GND_SMON "can be
        # tied to the system ground with an isolating ferrite bead" (Figure
        # 1); with no bead in the example catalogue it joins the main ground
        # directly, without that filter.
        smon_ground = fpga.pwr_vccaux_smon.Vn
        self.GND_SMON = Net(
            [
                smon_ground,
                fpga.VREFP_500,
                fpga.VREFN_500,
                fpga.VP_500,
                fpga.VN_500,
                fpga.pwr_vccint.Vn,
            ]
        )


class GtCalibration(Container):
    """Each transceiver group's calibration supply and reference resistor.

    AM002 (GTY) and AM017 (GTM), "Termination Resistor Calibration
    Circuit", connect the AVTTRCAL pin to the group's AVTT supply and to one
    pin of a 100 ohm precision resistor, and the resistor's other pin to
    RREF. Each group here does that on its own AVTT rail, so the AVTT
    capacitors decouple AVTTRCAL too. TE0950 rev 03 page 12 builds the same
    circuit for GTYP with R41, 100R 1%, the tolerance used here. DS959 v1.8
    Table 1 lists the GTY and GTM AVTTRCAL supplies with the same range as
    AVTT, 1.164 to 1.236 V.
    """

    def __init__(self, fpga: VP1002LPDDR4) -> None:
        groups = (
            (fpga.pwr_gty_avtt_rs, fpga.GTY_AVTTRCAL_RS, fpga.GTY_RREF_RS),
            (fpga.pwr_gtm_avtt_l, fpga.GTM_AVTTRCAL_L, fpga.GTM_RREF_L),
            (fpga.pwr_gtm_avtt_rn, fpga.GTM_AVTTRCAL_RN, fpga.GTM_RREF_RN),
        )
        self.r_rref = [
            Resistor(resistance=RREF_RESISTANCE, tolerance=AtMost(RREF_TOLERANCE))
            for _ in groups
        ]
        self.AVTT = [
            Net([avtt.Vp, rcal, r.p1])
            for (avtt, rcal, _), r in zip(groups, self.r_rref, strict=True)
        ]
        self.RREF = [
            rref + r.p2 for (_, _, rref), r in zip(groups, self.r_rref, strict=True)
        ]
