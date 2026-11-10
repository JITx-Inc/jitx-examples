"""JS4 verification design: code routes that make the constraints measure.

Not part of the shipping design. :py:class:`JS4ProofDesign` adds code
``Route``\\ s to :py:class:`~.main.JS4Circuit` for one byte lane, the clock,
the clock enable and one address bit of channel B, and nothing else, on pins
the VP1002's offer allows (memory byte 2 in byte slot 3, its DQ reordered).
JITX resolves the offer from the routes and measures each routed path against
the constraints of :py:mod:`.constraint`: DQS and CK intra-pair skew, each DQ
and DMI against DQS, CA0 and both CKE balls against CK, the CK minus DQS
window, and the delay of each CAC and data path against the trace length
budget. The CKE runs in a chain, FPGA pin to CKE0 to CKE1.

:py:class:`JS4TightenedDesign` has the same route code under
:py:data:`~.constraint.TIGHTENED_PARAMS`, a requirement change, and reports
each DQ and DMI skew against the tighter limit. The router can realize the
same route code differently under the changed constraints, so its measured
delays need not match :py:class:`JS4ProofDesign`'s.

What the proof shows is that the constraints bind: each routed path
reports a measurement. It does not show compliance:

- The routes run on inner layers, as UG863 asks: the CK and DQS pairs, CA0,
  two DQ bits and the CKE chain on L5, the rest on L3. Surface routes do not
  fit: no JS1 HDI single-ended structure's clearance fits between the
  Micron's 0.8 mm by 0.65 mm balls, and L3 alone does not hold every route.
  UG863 asks for a byte lane on one layer; this proof splits it.
- Each end drops through stacked JS1 microvias, with delay models, in the
  ball's pad, attached to the ball's port with ``PortAttachment``: two per
  end to L3, four to L5. That is 4 or 8 vias per signal, and 12 on the CKE chain, against
  UG863's budget of 2 per data, strobe, address or clock signal and 3 per
  CKE ("Physical Design Rules for LPDDR4/4x Signals").
- Length matching is off for each route (:py:data:`NO_LENGTH_MATCH`), so a
  skew lands where its route does; some miss their limits. Meeting them
  is length matching's work, which this proof leaves out.
- Each measured delay includes the FPGA pin's package delay and each via's
  delay (:py:mod:`.models`), so each routed group reads met or NOT MET on
  its measurement. Both are inputs, not characterizations: the package
  values are synthetic estimates, not AMD data, and the via model is a
  floor on the via's delay. A skew between two FPGA pins includes the
  difference of their package delays, which can carry it over its limit
  where the routes alone would not; a pair's two legs carry the same
  synthetic value, so a pair's skew is its routes'.

Run the issue report as :py:mod:`.main` shows, importing these designs
instead.
"""

from jitx.circuit import Route
from jitx.component import Component
from jitx.design import Design
from jitx.net import Port, PortAttachment
from jitx.via import Via

from jitxexamples.protocols.memory.lpddr4 import LPDDR4ConstraintParams

from ..js1_stackup_components.hdi_stackup.board import HDIBoard, HDISubstrate
from ..vp1002_lpddr4x.pinout import LPDDR4X_X32, Pos
from ..vp1002_lpddr4x.proof import (
    DQ_ORDER,
    NO_LENGTH_MATCH,
    L3,
    L5,
    L5_BITS,
    SLOT,
    pad_center,
)
from .constraint import TIGHTENED_PARAMS, UG863_PARAMS
from .main import JS4Circuit
from .models import MODELED_MICROVIAS

CAC_LAYER = L5
"Layer of channel B's CK pair, CKE chain and CA0: CAC and clock on one layer."


class JS4ProofCircuit(JS4Circuit):
    """:py:class:`~.main.JS4Circuit` plus the proof routes."""

    def __init__(self, params: LPDDR4ConstraintParams = UG863_PARAMS) -> None:
        super().__init__(params)
        self.proof_vias: list[Via] = []
        self.proof_attachments: list[PortAttachment] = []
        self.proof_routes: list[Route] = []
        for fpga_port, mem_port, layer in self.proof_ends():
            ends = [
                self._via_stack(self.fpga.fpga, fpga_port, layer),
                self._via_stack(self.memory, mem_port, layer),
            ]
            self.proof_routes.append(
                Route(ends[0], ends[1], layer=layer, config=NO_LENGTH_MATCH)
            )
        # Channel B's CKE: one FPGA pin to both memory CKE balls, in a chain.
        ch = self.memory.lpddr4.ch[1]
        cke_pin = self._pin(LPDDR4X_X32.fixed["CKE_B"])
        cke = [
            self._via_stack(self.fpga.fpga, cke_pin, CAC_LAYER),
            self._via_stack(self.memory, ch.cke[0], CAC_LAYER),
            self._via_stack(self.memory, ch.cke[1], CAC_LAYER),
        ]
        self.proof_routes += [
            Route(cke[0], cke[1], layer=CAC_LAYER, config=NO_LENGTH_MATCH),
            Route(cke[1], cke[2], layer=CAC_LAYER, config=NO_LENGTH_MATCH),
        ]

    def _via_stack(self, component: Component, port: Port, layer: int) -> Via:
        """Stack microvias in the port's pad down to ``layer``; return the
        bottom one."""
        at = pad_center(component, port)
        stack = [via().at(at) for via in MODELED_MICROVIAS[:layer]]
        self.proof_vias += stack
        self.proof_attachments += [PortAttachment(port, via) for via in stack]
        return stack[-1]

    def _pin(self, pos: Pos) -> Port:
        return self.fpga.fpga.xpio_triplet_pins()[0][pos.index].port

    def proof_ends(self) -> list[tuple[Port, Port, int]]:
        """FPGA pin, memory pin and layer of each proof route."""
        fixed = LPDDR4X_X32.fixed
        ch = self.memory.lpddr4.ch[1]
        lane = ch.d[0]
        dq_pins = list(SLOT.dq)
        ends = [
            (self._pin(SLOT.dqs_t), lane.dqs.p, L5),
            (self._pin(SLOT.dqs_c), lane.dqs.n, L5),
            (self._pin(SLOT.dmi), lane.dmi, L3),
            *(
                (self._pin(pos), lane.dq[bit], L5 if bit in L5_BITS else L3)
                for pos, bit in zip(dq_pins, DQ_ORDER, strict=True)
            ),
            (self._pin(fixed["CK_T_B"]), ch.ck.p, CAC_LAYER),
            (self._pin(fixed["CK_C_B"]), ch.ck.n, CAC_LAYER),
            (self._pin(fixed["CA0_B"]), ch.ca[0], CAC_LAYER),
        ]
        return ends


class JS4ProofDesign(Design):
    """The verification routes under UG863's limits."""

    board = HDIBoard()
    substrate = HDISubstrate()
    circuit = JS4ProofCircuit()


class JS4TightenedDesign(Design):
    """The same routes under :py:data:`~.constraint.TIGHTENED_PARAMS`."""

    board = HDIBoard()
    substrate = HDISubstrate()
    circuit = JS4ProofCircuit(TIGHTENED_PARAMS)
