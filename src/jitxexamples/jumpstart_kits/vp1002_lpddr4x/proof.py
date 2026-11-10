"""Proof routes for the VP1002's LPDDR4X offer: a legal assignment and an
illegal one.

Not part of any shipping design. :py:class:`SwapProofCircuit` places the
:py:class:`~.circuit.VP1002LPDDR4X` and a Micron MT53E1G32D2FW on JS1's HDI
board, requires the offer, nets channel B's first byte lane to the memory,
and code-routes that lane: the DQS pair, DMI and the eight DQ, each end
dropped through stacked microvias in its pad to an inner layer.

- :py:class:`SwapProofDesign` routes memory byte 2 (channel B, DQ16 to DQ23)
  to byte slot 3, the slot :py:data:`~.pinout.LPDDR4X_X32` gives byte 3 by
  default, with its DQ reordered: a byte swap and a bit swap the offer
  allows. JITX resolves the offer from the routes.
- :py:class:`IllegalSwapDesign` routes the same lane but sends one DQ bit to
  a pin of byte slot 0, a channel A slot (ball AT20). No option allows that,
  so JITX drops the route and reports
  ``Code route dropped: its ends are on different nets``.

The legal design's report holds only the routing group, ``met Satisfied``
(every code route was made); the illegal design's holds the dropped route.
Measuring the routed paths needs SI constraints on
them; the JS4 kit's reference,
:py:mod:`jitxexamples.jumpstart_kits.js4_si_constraints`, adds them.
"""

from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.design import Design
from jitx.inspect import extract
from jitx.landpattern import Pad, PadMapping
from jitx.net import Port, PortAttachment
from jitx.via import Via

from jitxexamples.components.memories.MT53E1G32D2FW_046_WT_B import (
    MT53E1G32D2FW_046_WT_B,
)

from ..js1_stackup_components.hdi_stackup.board import HDIBoard, HDISubstrate
from .bundles import VersalLPDDR4X
from .circuit import VP1002LPDDR4X
from .pinout import LPDDR4X_X32, Pos

SLOT = LPDDR4X_X32.slots[3]
"Byte slot 3: third bank (702), DQS on N6, DMI on N7."

DQ_ORDER = (5, 2, 7, 0, 3, 6, 1, 4)
"Memory DQ bit routed to each pin of ``SLOT.dq`` in turn: a bit swap."

ILLEGAL_PIN = Pos(1, 2, 4)
"""A DQ pin of byte slot 0 (channel A), ``IO_L8P_N2P4_M0P70_701`` at ball
AT20: not allowed for a channel B bit."""

L3, L5 = 2, 4
"Layer indices of the first two stripline layers."

L5_BITS = frozenset({3, 7})
"Memory DQ bits routed on L5 with DQS; the rest run on L3."

MICROVIAS = (
    HDISubstrate.MicroVia_L1_L2,
    HDISubstrate.MicroVia_L2_L3,
    HDISubstrate.MicroVia_L3_L4,
    HDISubstrate.MicroVia_L4_L5,
)
"JS1's microvias, top down: stacking the first ``n`` reaches layer ``n``."

NO_LENGTH_MATCH = Route.Config(envelope_overhead=0)
"""Length matching off for the route. The router still chooses the route's
path, and can choose a different one when the design's constraints change."""


def pad_center(component: Component, port: Port) -> tuple[float, float]:
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


class SwapProofCircuit(Circuit):
    """The FPGA and the memory, channel B's first byte lane netted and
    routed."""

    illegal = False

    def __init__(self) -> None:
        self.fpga = VP1002LPDDR4X()
        self.fpga.fpga.at(0, 12)
        self.memory = MT53E1G32D2FW_046_WT_B().at(10, -14.5, rotate=180)
        bus = self.fpga.require(VersalLPDDR4X)
        src = bus.ch[1].d[0]
        lane = self.memory.lpddr4.ch[1].d[0]
        self.DQS = src.dqs + lane.dqs
        self.DMI = src.dmi + lane.dmi
        self.DQ = [a + b for a, b in zip(src.dq, lane.dq, strict=True)]

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
        ]
        self.proof_vias: list[Via] = []
        self.proof_attachments: list[PortAttachment] = []
        self.proof_routes = [
            Route(
                self._via_stack(self.fpga.fpga, fpga_port, layer),
                self._via_stack(self.memory, mem_port, layer),
                layer=layer,
                config=NO_LENGTH_MATCH,
            )
            for fpga_port, mem_port, layer in ends
        ]

    def _pin(self, pos: Pos) -> Port:
        return self.fpga.fpga.xpio_triplet_pins()[0][pos.index].port

    def _via_stack(self, component: Component, port: Port, layer: int) -> Via:
        """Stack microvias in the port's pad down to ``layer``; return the
        bottom one."""
        at = pad_center(component, port)
        stack = [via().at(at) for via in MICROVIAS[:layer]]
        self.proof_vias += stack
        self.proof_attachments += [PortAttachment(port, via) for via in stack]
        return stack[-1]


class IllegalSwapCircuit(SwapProofCircuit):
    """The same lane with one DQ bit sent to a channel A pin."""

    illegal = True


class SwapProofDesign(Design):
    """Legal assignment, code-routed."""

    board = HDIBoard()
    substrate = HDISubstrate()
    circuit = SwapProofCircuit()


class IllegalSwapDesign(Design):
    """Illegal assignment, code-routed: the route is dropped."""

    board = HDIBoard()
    substrate = HDISubstrate()
    circuit = IllegalSwapCircuit()
