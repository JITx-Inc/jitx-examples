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
:py:data:`~jitxexamples.jumpstart_kits.vp1002_lpddr4.package_delays.SYNTHETIC_CSV`,
whose values are synthetic estimates, not AMD data. The memory's pins get no
model: UG863's table asks only for the adaptive SoC's delays.

Via delay
---------

Every via of the reference substrate carries a first-order delay model for
each pair of copper layers it joins
(:py:func:`~jitxexamples.substrates.reference_18layer.via_models`), so a
route through any of them is measured. The models carry no loss, so a
loss limit measures the trace alone.
"""

from __future__ import annotations

import csv
from pathlib import Path

from jitx.net import Port
from jitx.si import TerminatingPinModel


from ..js1_stackup_components.versal_fpga.tools.generate_pinout import ball_to_rc
from ..js1_stackup_components.versal_fpga.xcvp1002 import XCVP1002

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
