"""JS4 Part 3: SI constraints on the VP1002 to Micron LPDDR4 link.

:py:class:`JS4SIConstraintsCircuit` takes Part 2's board
(:py:mod:`.part2_power`): Part 1's fanned-out board, its memory placed
(:py:mod:`.part1_fanout_escape`), which already applies the ball-field
pair structure (:py:mod:`.ball_field`), with Part 2's decoupling, plane pours
and power rules. It applies UG863's skew limits, four of them tightened to
the kit's layout targets, and its trace length budget
(:py:mod:`.constraint`), an insertion loss limit, the package delay pin
models, the reference planes and UG863's spacing (:py:mod:`.rules`).

Each FPGA pin of memory triplet M0, which holds every pin the offer uses,
carries its package delay as a :py:class:`~jitx.si.TerminatingPinModel`,
read from the synthetic estimates the part package supplies
(:py:mod:`.models`); a real design reads its Vivado export instead. JITX
picks the pin assignment when the board is routed, so before routing each
constrained path reports its pin unassigned, or for CKE no path.

CAC and data take the substrate's 46 ohm single-ended structure and CK and
DQS its 85 ohm differential structure: the structures inside UG863's 45 ohm
and 82 ohm +/-10% windows (:py:mod:`.constraint`). Inside a ball field a
pair's route segment takes a narrower structure by a tag on its ``Route``;
a single-ended line keeps its own. UG863's spacing holds the byte lanes
and channels apart.

The loss limit is :py:data:`LOSS_LIMIT_DB` on every LPDDR4 signal, standing
in for an SI team's budget, not a UG863 value (:py:mod:`.constraint`, "Not
applied"). The substrate's loss model
is dielectric loss at 10 GHz only, about 0.0068 dB/mm on the 46 ohm
stripline, so a 75 mm path reads about 0.5 dB.

To see the report, save this as a script in the project root and run it
with the project's runtime running::

    import jitx

    from jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part3_si_constraints import (
        JS4SIConstraintsDesign,
    )


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(JS4SIConstraintsDesign).issues(satisfied=True, wait=30)
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
imports every ``.py`` file under the project root. The design needs the
parts chain :py:mod:`.base` describes.
"""

from dataclasses import replace

from jitx.design import Design
from jitx.si import ReferencePlanes

from jitxexamples.protocols.memory.lpddr4 import LPDDR4ConstraintParams
from jitxexamples.substrates.reference_18layer import (
    STRIPLINE_LAYERS,
    Reference18Board,
    Reference18Substrate,
    nearest_plane_height,
)

from ..vp1002_lpddr4.package_delays import SYNTHETIC_CSV
from .part2_power import JS4PowerCircuit
from .constraint import KIT_PARAMS, VersalLPDDR4Constraint, length_budget
from .models import package_pin_models
from .rules import spacing_rules

LOSS_LIMIT_DB = 1.0
"""Insertion loss limit, dB, on every LPDDR4 signal, standing in for an SI
team's budget. Not a UG863 value."""


class JS4SIConstraintsCircuit(JS4PowerCircuit):
    """:py:class:`~.part2_power.JS4PowerCircuit` with the SI
    constraints, the pin models and the spacing rules of Part 3.

    Args:
        params: Skew limits; by default :py:data:`~.constraint.KIT_PARAMS`,
            UG863's with four rules tightened to 20% of their limit.
        loss: Insertion loss limit in dB on every signal, set into
            ``params``; :py:data:`LOSS_LIMIT_DB` by default.
    """

    def __init__(
        self,
        params: LPDDR4ConstraintParams = KIT_PARAMS,
        loss: float = LOSS_LIMIT_DB,
    ) -> None:
        super().__init__()
        # Package delay on each FPGA pin of triplet M0, from the synthetic
        # estimates the part package supplies; a real design reads its Vivado
        # export instead.
        self.package_delays = package_pin_models(self.fpga.fpga, SYNTHETIC_CSV)
        bus = self.lpddr4_bus()
        mem = self.memory.memory.lpddr4
        # The budget is set on the inner layers the 46 ohm structure covers:
        # every stripline layer but L16_SIG6, whose 46 ohm entry the drawing
        # strikes.
        se = Reference18Substrate.SE_46
        inner = tuple(layer for layer in STRIPLINE_LAYERS if layer in se.layers)
        with ReferencePlanes(self.gnd_net):
            self.lpddr4_si = VersalLPDDR4Constraint(
                diff_structure=Reference18Substrate.DRS_85,
                se_structure=se,
                params=replace(params, loss=loss),
                max_delay=length_budget(se, inner),
            )
            self.lpddr4_si.constrain(bus, mem)

        # UG863's spacing between byte lanes and channels at the inner layers'
        # H (:py:mod:`.rules`). Part 1 applies the ball-field pair structure.
        self.spacing_rules = spacing_rules(
            byte_lanes=[
                [*dq, dqs, dmi]
                for dq, dqs, dmi in zip(self.DQ, self.DQS, self.DMI, strict=True)
            ],
            cac_clock=[
                [*ca, *cs, cke, ck]
                for ca, cs, cke, ck in zip(
                    self.CA, self.CS, self.CKE, self.CK, strict=True
                )
            ],
            pairs=[*self.DQS, *self.CK],
            height=max(nearest_plane_height(layer) for layer in inner),
        )


class JS4SIConstraintsDesign(Design):
    """Part 3's reference: Part 2's design with the SI constraints, before
    any route but Part 1's escapes."""

    board = Reference18Board()
    substrate = Reference18Substrate()
    circuit = JS4SIConstraintsCircuit()
