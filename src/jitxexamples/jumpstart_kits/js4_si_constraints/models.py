"""Delay models the measurements need: the FPGA's package and the board's vias.

Package delay
-------------

UG863's LPDDR4/4x timing table says "Include adaptive SoC package delays for
all skew calculations", and its "Required Memory Routing Guidelines for All
Interfaces" says "Include package delay in routing constraints when
determining signal trace lengths unless otherwise specified", using "the
midpoint/average between the minimum and maximum values".
:py:func:`package_pin_models` reads a package delay CSV in the shape of
Vivado's I/O ports export (UG899 Appendix A) and gives each FPGA pin with a
delay a :py:class:`~jitx.si.TerminatingPinModel` at that midpoint, so JITX
adds the pin's package delay to every path that ends on it, delay limits
included (:py:mod:`.constraint` says how the length rule reads that).

The design reads
:py:data:`~jitxexamples.jumpstart_kits.vp1002_lpddr4x.package_delays.SYNTHETIC_CSV`,
whose values are synthetic estimates, not AMD data. The memory's pins get no
model: UG863's table asks only for the adaptive SoC's delays.

Via delay
---------

JS1's vias carry no model, so JITX would measure through each with a
placeholder and leave every routed group unresolved. :py:data:`MODELED_MICROVIAS`
are JS1's four microvias with a first-order delay model: the barrel's transit
time, delay = D * sqrt(Dk) / c, where D runs from the middle of the via's top
copper to the middle of its bottom copper and Dk is the dielectric's. It
leaves out pad and antipad loading, so it is a floor on the via's delay, not
a characterization. No loss is modeled; the constraint sets no loss limit.
"""

from __future__ import annotations

import csv
from math import sqrt
from pathlib import Path

from jitx.net import Port
from jitx.si import PinModel, TerminatingPinModel
from jitx.stackup import Conductor, Dielectric
from jitx.via import Via

from ..js1_stackup_components.hdi_stackup.board import (
    BuildUpPrepreg,
    HDISubstrate,
    OuterCopper,
    PlaneCopper,
    SignalCopper,
)
from ..js1_stackup_components.versal_fpga.tools.generate_pinout import ball_to_rc
from ..js1_stackup_components.versal_fpga.xcvp1002 import XCVP1002

C_MM_PER_S = 299_792_458_000.0
"Speed of light in mm per second."

BALL = "Pin Number"
MIN_DELAY = "Min Trace Delay (ps)"
MAX_DELAY = "Max Trace Delay (ps)"


def read_package_delays(path: Path) -> dict[str, float]:
    """Midpoint package delay in seconds for each ball a Vivado-style I/O
    ports CSV gives a delay, read by column name. Comment lines start with
    ``#``; a row with a blank delay (an export lists every pin) is skipped."""
    with path.open(encoding="utf-8", newline="") as f:
        rows = csv.DictReader(line for line in f if not line.startswith("#"))
        return {
            row[BALL]: (float(row[MIN_DELAY]) + float(row[MAX_DELAY])) / 2 * 1e-12
            for row in rows
            if (row[MIN_DELAY] or "").strip() and (row[MAX_DELAY] or "").strip()
        }


def package_pin_models(fpga: XCVP1002, path: Path) -> list[TerminatingPinModel]:
    """A :py:class:`~jitx.si.TerminatingPinModel` at the midpoint delay, and no
    loss, for each of the FPGA's balls in the CSV at ``path``."""
    delays = read_package_delays(path)
    by_position = {rc: port for port, rc in fpga.ball_assignments()}
    models: list[TerminatingPinModel] = []
    for ball, delay in delays.items():
        port: Port = by_position[ball_to_rc(ball)]
        models.append(TerminatingPinModel(port, delay=delay, loss=0.0))
    return models


def via_delay(
    top: type[Conductor], dielectric: type[Dielectric], bottom: type[Conductor]
) -> float:
    """First-order delay in seconds of a via through one dielectric layer,
    from mid-copper to mid-copper."""
    t_top, t_mid, t_bottom = top.thickness, dielectric.thickness, bottom.thickness
    dk = dielectric.dielectric_coefficient
    if t_top is None or t_mid is None or t_bottom is None or dk is None:
        raise ValueError(f"{top}, {dielectric} or {bottom} lacks a thickness or Dk")
    return (t_top / 2 + t_mid + t_bottom / 2) * sqrt(dk) / C_MM_PER_S


class MicroVia_L1_L2(HDISubstrate.MicroVia_L1_L2):
    """JS1's L1 to L2 microvia, through the outer copper, with its delay."""

    models = {
        (0, 1): PinModel(via_delay(OuterCopper, BuildUpPrepreg, PlaneCopper), 0.0)
    }


class MicroVia_L2_L3(HDISubstrate.MicroVia_L2_L3):
    """JS1's L2 to L3 microvia with its delay."""

    models = {
        (1, 2): PinModel(via_delay(PlaneCopper, BuildUpPrepreg, SignalCopper), 0.0)
    }


class MicroVia_L3_L4(HDISubstrate.MicroVia_L3_L4):
    """JS1's L3 to L4 microvia with its delay."""

    models = {
        (2, 3): PinModel(via_delay(SignalCopper, BuildUpPrepreg, PlaneCopper), 0.0)
    }


class MicroVia_L4_L5(HDISubstrate.MicroVia_L4_L5):
    """JS1's L4 to L5 microvia with its delay."""

    models = {
        (3, 4): PinModel(via_delay(PlaneCopper, BuildUpPrepreg, SignalCopper), 0.0)
    }


MODELED_MICROVIAS: tuple[type[Via], ...] = (
    MicroVia_L1_L2,
    MicroVia_L2_L3,
    MicroVia_L3_L4,
    MicroVia_L4_L5,
)
"JS1's microvias with delay models, top down: stacking the first ``n`` reaches layer ``n``."
