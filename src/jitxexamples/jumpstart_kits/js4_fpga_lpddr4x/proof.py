"""JS4 verification designs: code routes that pick, or break, a pin assignment.

Not part of the shipping design. Each adds code ``Route``\\ s to
:py:class:`~.main.JS4Circuit` for one byte lane, the clock, the clock enable
and one address bit of channel B, and nothing else:

- :py:class:`JS4ProofDesign` routes a legal assignment. Memory byte 2
  (channel B, DQ16 to DQ23) lands in byte slot 3, the slot
  :py:data:`~.pinout.OPTIMUM_X32_FLIPPED` gives byte 3 by default, so the routes
  choose a byte swap (rule 4) and a reordering of the eight DQ (rule 3).
  JITX resolves the ``provide`` options from the routes and measures each
  routed path: DQS and CK intra-pair skew, each DQ and DMI against DQS,
  CA0 and both CKE balls against CK, and the CK minus DQS window. The CKE
  runs in a chain, FPGA pin to CKE0 to CKE1.
- :py:class:`JS4IllegalDesign` routes the same set but sends one DQ bit to a
  pin of byte slot 0, a channel A slot. No option allows that, so the route
  is dropped and the path stays unassigned.

What the proof shows is that the constraints bind: each routed path
reports a measured skew. It does not show compliance:

- The routes run on inner layers, as UG863 asks: the DQS pair, two DQ bits
  and the CKE chain on L5, the rest on L3. Surface routes do not fit: no
  JS1 HDI single-ended structure's clearance fits between the Micron's
  0.8 mm by 0.65 mm balls, and L3 alone does not hold every route. UG863
  asks for a byte lane on one layer; this proof splits it.
- Each end drops through stacked JS1 microvias in the ball's pad, attached
  to the ball's port with ``PortAttachment``: two per end to L3, four to
  L5. That is 4 or 8 vias per signal, and 12 on the CKE chain, against
  UG863's budget of 2 per data, strobe, address or clock signal and 3 per
  CKE ("Physical Design Rules for LPDDR4/4x Signals").
- The routes are not length matched, so some skews miss their targets.
- The JS1 vias carry no delay model: JITX uses a placeholder for each and
  lists that as an issue, so every routed group reads NOT MET whatever its
  skew. The measured delays also leave out the VP1002 package delay.

Run the issue report as :py:mod:`.main` shows, importing these designs
instead.
"""

from jitx.circuit import Route
from jitx.component import Component
from jitx.design import Design
from jitx.inspect import extract
from jitx.landpattern import Pad, PadMapping
from jitx.net import Port, PortAttachment
from jitx.via import Via

from ..js1_stackup_components.hdi_stackup.board import HDIBoard, HDISubstrate
from .main import JS4Circuit
from .pinout import OPTIMUM_X32_FLIPPED, Pos

SLOT = OPTIMUM_X32_FLIPPED.slots[3]
"Byte slot 3: third bank (702), DQS on N6, DMI on N7."

DQ_ORDER = (5, 2, 7, 0, 3, 6, 1, 4)
"Memory DQ bit routed to each pin of ``SLOT.dq`` in turn: a bit swap."

ILLEGAL_PIN = Pos(1, 2, 4)
"A DQ pin of byte slot 0 (channel A): not allowed for a channel B bit."

L3, L5 = 2, 4
"Layer indices of the first two stripline layers."

CKE_LAYER = L5
"Layer of the channel B CKE chain."

L5_BITS = frozenset({3, 7})
"Memory DQ bits routed on L5 with DQS; the rest of the set runs on L3."

_MICROVIAS = (
    HDISubstrate.MicroVia_L1_L2,
    HDISubstrate.MicroVia_L2_L3,
    HDISubstrate.MicroVia_L3_L4,
    HDISubstrate.MicroVia_L4_L5,
)


def _pad_center(component: Component, port: Port) -> tuple[float, float]:
    """Board position of the pad a single-pad port maps to."""
    for mapping in extract(component, PadMapping):
        try:
            pads = mapping[port]
        except KeyError:
            continue
        pad = pads if isinstance(pads, Pad) else pads[0]
        if component.transform is None or pad.transform is None:
            raise ValueError(f"{component} or its pad for {port} is not placed")
        return component.transform * (pad.transform * (0.0, 0.0))
    raise KeyError(f"{port} has no pad")


class JS4ProofCircuit(JS4Circuit):
    """:py:class:`~.main.JS4Circuit` plus the legal proof routes."""

    illegal = False

    def __init__(self) -> None:
        super().__init__()
        self.proof_vias: list[Via] = []
        self.proof_attachments: list[PortAttachment] = []
        self.proof_routes: list[Route] = []
        for fpga_port, mem_port, layer in self.proof_ends():
            ends = [
                self._via_stack(self.fpga.fpga, fpga_port, layer),
                self._via_stack(self.memory, mem_port, layer),
            ]
            self.proof_routes.append(Route(ends[0], ends[1], layer=layer))
        # Channel B's CKE: one FPGA pin to both memory CKE balls, in a chain.
        ch = self.memory.lpddr4.ch[1]
        cke_pin = self._pin(OPTIMUM_X32_FLIPPED.fixed["CKE_B"])
        cke = [
            self._via_stack(self.fpga.fpga, cke_pin, CKE_LAYER),
            self._via_stack(self.memory, ch.cke[0], CKE_LAYER),
            self._via_stack(self.memory, ch.cke[1], CKE_LAYER),
        ]
        self.proof_routes += [
            Route(cke[0], cke[1], layer=CKE_LAYER),
            Route(cke[1], cke[2], layer=CKE_LAYER),
        ]

    def _via_stack(self, component: Component, port: Port, layer: int) -> Via:
        """Stack microvias in the port's pad down to ``layer``; return the
        bottom one."""
        at = _pad_center(component, port)
        stack = [via().at(at) for via in _MICROVIAS[:layer]]
        self.proof_vias += stack
        self.proof_attachments += [PortAttachment(port, via) for via in stack]
        return stack[-1]

    def _pin(self, pos: Pos) -> Port:
        return self.fpga.fpga.xpio_triplet_pins()[0][pos.index].port

    def proof_ends(self) -> list[tuple[Port, Port, int]]:
        """FPGA pin, memory pin and layer of each proof route."""
        fixed = OPTIMUM_X32_FLIPPED.fixed
        ch = self.memory.lpddr4.ch[1]
        lane = ch.d[0]
        dq_pins = list(SLOT.dq)
        if self.illegal:
            dq_pins[0] = ILLEGAL_PIN
        ends = [
            (self._pin(SLOT.dqs_t), lane.dqs.p, L5),
            (self._pin(SLOT.dqs_c), lane.dqs.n, L5),
            (self._pin(SLOT.dmi), lane.dmi, L3),
            *(
                (self._pin(pos), lane.dq[bit], L5 if bit in L5_BITS else L3)
                for pos, bit in zip(dq_pins, DQ_ORDER, strict=True)
            ),
            (self._pin(fixed["CK_T_B"]), ch.ck.p, L3),
            (self._pin(fixed["CK_C_B"]), ch.ck.n, L3),
            (self._pin(fixed["CA0_B"]), ch.ca[0], L3),
        ]
        return ends


class JS4IllegalProofCircuit(JS4ProofCircuit):
    """The proof routes with one DQ bit sent to a channel A pin."""

    illegal = True


class JS4ProofDesign(Design):
    """Legal assignment, code-routed."""

    board = HDIBoard()
    substrate = HDISubstrate()
    circuit = JS4ProofCircuit()


class JS4IllegalDesign(Design):
    """Illegal assignment, code-routed: the route is rejected."""

    board = HDIBoard()
    substrate = HDISubstrate()
    circuit = JS4IllegalProofCircuit()
