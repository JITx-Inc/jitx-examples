"""XCVP1002 wrapped with the circuit boundary a board designer consumes.

Pattern
    The standard JITX FPGA-wrapper shape: one ``Power`` port per supply
    rail, named power nets, distinct ground domains, and GT transceiver
    quads exposed as bundle ports wired through the ``>>`` topology
    operator.

    One deliberate discipline: wrapper code in the wild often resolves
    component pins with ``getattr`` name composition
    (``f"GTM_TXP{lane}_{bank}"``); this repo's conventions forbid
    reflection, so the wiring here consumes the generated structural
    :meth:`~.xcvp1002.XCVP1002.gtm_quad_pins` groupings instead — every
    pin reference is an explicit attribute.

Scope (JS1 · Part 3)
    Power/ground and the six GTM quads only. XPIO / PS-MIO bank bundles,
    GPIO mass-``Provide`` pin assignment, and per-net via fanout are board-
    level concerns deferred to JS2. Unwrapped pins remain reachable via
    ``self.fpga``.

Ground domains (three, kept distinct)
    * main ``GND`` — all 689 ``GND`` balls, both ``RSVDGND`` balls, and
      every main rail's ``Vn``.
    * ``GND_SMON`` — the system-monitor analog ground: ``pwr_vccaux_smon.Vn``
      and the ``GND_SMON`` ball only.
    * ``GND_SENSE`` — the ``VCCINT`` Kelvin sense return:
      ``pwr_vccint_sense.Vn`` and the ``GND_SENSE`` ball only.

Rail roster
    :meth:`XCVP1002Circuit.rail_ties` — taken verbatim from the generated
    component's rail inventory (the AMD pinout file is the ground truth);
    no rail invented, none dropped. The roster is a method returning fresh
    records because a ``Port`` may have only one home in the design tree.
"""

from dataclasses import dataclass
from enum import Enum

from jitx import Circuit, Net
from jitx.common import Power
from jitx.net import Port

from .bundles import GTMQuad
from .xcvp1002 import XCVP1002


class GroundDomain(Enum):
    MAIN = "GND"
    SMON = "GND_SMON"
    SENSE = "GND_SENSE"


@dataclass(frozen=True)
class RailTie:
    """One supply rail: boundary port, component pins, ground domain."""

    label: str
    port: Power
    pins: tuple[Port, ...]
    domain: GroundDomain = GroundDomain.MAIN


class XCVP1002Circuit(Circuit):
    """VP1002 with power/ground and GTM transceiver boundary ports."""

    # ---- Core / fabric rails ----
    pwr_vccint = Power()
    pwr_vcc_soc = Power()
    pwr_vccaux = Power()
    pwr_vcc_ram = Power()
    pwr_vcc_io = Power()

    # ---- Processing system / platform management rails ----
    pwr_vcc_psfp = Power()
    pwr_vcc_pslp = Power()
    pwr_vcc_pmc = Power()
    pwr_vccaux_pmc = Power()

    # ---- Per-bank I/O supplies ----
    pwr_vcco_500 = Power()
    pwr_vcco_501 = Power()
    pwr_vcco_502 = Power()
    pwr_vcco_503 = Power()
    pwr_vcco_700 = Power()
    pwr_vcco_701 = Power()
    pwr_vcco_702 = Power()

    # ---- GT transceiver analog rails ----
    pwr_gtm_avcc_l = Power()
    pwr_gtm_avcc_rn = Power()
    pwr_gtm_avccaux_l = Power()
    pwr_gtm_avccaux_rn = Power()
    pwr_gtm_avtt_l = Power()
    pwr_gtm_avtt_rn = Power()
    pwr_gty_avcc_rs = Power()
    pwr_gty_avccaux_rs = Power()
    pwr_gty_avtt_rs = Power()
    pwr_vccint_gt_l = Power()
    pwr_vccint_gt_r = Power()

    # ---- Single-ball rails ----
    pwr_vcc_batt = Power()
    pwr_vcc_fuse = Power()

    # ---- Separate ground domains ----
    pwr_vccaux_smon = Power()  # Vn ties to GND_SMON, not main GND
    pwr_vccint_sense = Power()  # Kelvin pair: Vn ties to GND_SENSE only

    # ---- System-monitor analog inputs (single-net boundary pins) ----
    VP_500 = Port()
    VN_500 = Port()
    VREFP_500 = Port()
    VREFN_500 = Port()

    # ---- GT bias / calibration pins (one external resistor each) ----
    GTM_AVTTRCAL_L = Port()
    GTM_RREF_L = Port()
    GTM_AVTTRCAL_RN = Port()
    GTM_RREF_RN = Port()
    GTY_AVTTRCAL_RS = Port()
    GTY_RREF_RS = Port()

    def rail_ties(self) -> list[RailTie]:
        """The full supply-rail roster, fresh records each call."""
        fpga = self.fpga
        return [
            RailTie("VCCINT", self.pwr_vccint, tuple(fpga.VCCINT)),
            RailTie("VCC_SOC", self.pwr_vcc_soc, tuple(fpga.VCC_SOC)),
            RailTie("VCCAUX", self.pwr_vccaux, tuple(fpga.VCCAUX)),
            RailTie("VCC_RAM", self.pwr_vcc_ram, tuple(fpga.VCC_RAM)),
            RailTie("VCC_IO", self.pwr_vcc_io, tuple(fpga.VCC_IO)),
            RailTie("VCC_PSFP", self.pwr_vcc_psfp, tuple(fpga.VCC_PSFP)),
            RailTie("VCC_PSLP", self.pwr_vcc_pslp, tuple(fpga.VCC_PSLP)),
            RailTie("VCC_PMC", self.pwr_vcc_pmc, tuple(fpga.VCC_PMC)),
            RailTie("VCCAUX_PMC", self.pwr_vccaux_pmc, tuple(fpga.VCCAUX_PMC)),
            RailTie("VCCO_500", self.pwr_vcco_500, tuple(fpga.VCCO_500)),
            RailTie("VCCO_501", self.pwr_vcco_501, tuple(fpga.VCCO_501)),
            RailTie("VCCO_502", self.pwr_vcco_502, tuple(fpga.VCCO_502)),
            RailTie("VCCO_503", self.pwr_vcco_503, tuple(fpga.VCCO_503)),
            RailTie("VCCO_700", self.pwr_vcco_700, tuple(fpga.VCCO_700)),
            RailTie("VCCO_701", self.pwr_vcco_701, tuple(fpga.VCCO_701)),
            RailTie("VCCO_702", self.pwr_vcco_702, tuple(fpga.VCCO_702)),
            RailTie("GTM_AVCC_L", self.pwr_gtm_avcc_l, tuple(fpga.GTM_AVCC_L)),
            RailTie("GTM_AVCC_RN", self.pwr_gtm_avcc_rn, tuple(fpga.GTM_AVCC_RN)),
            RailTie("GTM_AVCCAUX_L", self.pwr_gtm_avccaux_l, tuple(fpga.GTM_AVCCAUX_L)),
            RailTie(
                "GTM_AVCCAUX_RN", self.pwr_gtm_avccaux_rn, tuple(fpga.GTM_AVCCAUX_RN)
            ),
            RailTie("GTM_AVTT_L", self.pwr_gtm_avtt_l, tuple(fpga.GTM_AVTT_L)),
            RailTie("GTM_AVTT_RN", self.pwr_gtm_avtt_rn, tuple(fpga.GTM_AVTT_RN)),
            RailTie("GTY_AVCC_RS", self.pwr_gty_avcc_rs, tuple(fpga.GTY_AVCC_RS)),
            RailTie(
                "GTY_AVCCAUX_RS", self.pwr_gty_avccaux_rs, tuple(fpga.GTY_AVCCAUX_RS)
            ),
            RailTie("GTY_AVTT_RS", self.pwr_gty_avtt_rs, tuple(fpga.GTY_AVTT_RS)),
            RailTie("VCCINT_GT_L", self.pwr_vccint_gt_l, tuple(fpga.VCCINT_GT_L)),
            RailTie("VCCINT_GT_R", self.pwr_vccint_gt_r, tuple(fpga.VCCINT_GT_R)),
            RailTie("VCC_BATT", self.pwr_vcc_batt, (fpga.VCC_BATT,)),
            RailTie("VCC_FUSE", self.pwr_vcc_fuse, (fpga.VCC_FUSE,)),
            RailTie(
                "VCCAUX_SMON",
                self.pwr_vccaux_smon,
                (fpga.VCCAUX_SMON,),
                GroundDomain.SMON,
            ),
            RailTie(
                "VCCINT_SENSE",
                self.pwr_vccint_sense,
                (fpga.VCCINT_SENSE,),
                GroundDomain.SENSE,
            ),
        ]

    def __init__(self):
        self.fpga = XCVP1002()
        fpga = self.fpga

        # GTM quads: bundle boundary ports wired lane-for-lane onto the
        # component through pass-through topology segments, so SI
        # constraints can attach at the bundle in a board design.
        quad_pins = fpga.gtm_quad_pins()
        self.gtm: dict[int, GTMQuad] = {bank: GTMQuad() for bank in quad_pins}
        links = []
        for bank, quad in self.gtm.items():
            pins = quad_pins[bank]
            for lane, lane_pair in enumerate(quad.L):
                links.append(lane_pair.TX.p >> pins.txp[lane])
                links.append(lane_pair.TX.n >> pins.txn[lane])
                links.append(lane_pair.RX.p >> pins.rxp[lane])
                links.append(lane_pair.RX.n >> pins.rxn[lane])
            for i, refclk in enumerate(quad.REFCLK):
                links.append(refclk.p >> pins.refclkp[i])
                links.append(refclk.n >> pins.refclkn[i])
        self.gtm_links = links

        # Sysmon analog inputs and GT bias pins pass straight through.
        self.analog_nets = [
            self.VP_500 + fpga.VP_500,
            self.VN_500 + fpga.VN_500,
            self.VREFP_500 + fpga.VREFP_500,
            self.VREFN_500 + fpga.VREFN_500,
            self.GTM_AVTTRCAL_L + fpga.GTM_AVTTRCAL_L,
            self.GTM_RREF_L + fpga.GTM_RREF_L,
            self.GTM_AVTTRCAL_RN + fpga.GTM_AVTTRCAL_RN,
            self.GTM_RREF_RN + fpga.GTM_RREF_RN,
            self.GTY_AVTTRCAL_RS + fpga.GTY_AVTTRCAL_RS,
            self.GTY_RREF_RS + fpga.GTY_RREF_RS,
        ]

        # One named net per supply rail, spanning the boundary port's Vp
        # and every ball of the rail; Vn joins the rail's ground domain.
        self.gnd_net = Net(name=GroundDomain.MAIN.value)
        self.gnd_smon_net = Net(name=GroundDomain.SMON.value)
        self.gnd_sense_net = Net(name=GroundDomain.SENSE.value)
        grounds = {
            GroundDomain.MAIN: self.gnd_net,
            GroundDomain.SMON: self.gnd_smon_net,
            GroundDomain.SENSE: self.gnd_sense_net,
        }
        self.rail_nets: list[Net] = []
        for tie in self.rail_ties():
            net = Net(name=tie.label)
            net += tie.port.Vp
            for pin in tie.pins:
                net += pin
            grounds[tie.domain] += tie.port.Vn
            self.rail_nets.append(net)

        # Main ground spans every GND and RSVDGND ball; the SMON and
        # sense domains get only their dedicated return balls.
        for pin in fpga.GND:
            self.gnd_net += pin
        for pin in fpga.RSVDGND:
            self.gnd_net += pin
        self.gnd_smon_net += fpga.GND_SMON
        self.gnd_sense_net += fpga.GND_SENSE
