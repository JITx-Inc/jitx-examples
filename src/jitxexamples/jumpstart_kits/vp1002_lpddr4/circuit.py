"""The JS1 VP1002 with one LPDDR4 x32 interface offered on banks 702 and 701.

The offer is :py:data:`~.pinout.LPDDR4_X32`, built as two levels of
``provide``:

- Per byte slot, :py:class:`~.bundles.Slot0Bit` to ``Slot3Bit``: each of the
  slot's eight DQ pins, offered with ``all_of``. Taking eight of them in any
  order is the bit swap within a byte.
- :py:class:`~.bundles.VersalLPDDR4`, offered with ``one_of``: four options,
  one per allowed byte-to-slot order (the byte swap within a channel). Each
  option maps the fixed pins, the slot's DQS and DMI, and the eight DQ ports
  to eight pins required from the slot.

Together they offer every byte swap and bit swap AMD's rules allow on this
layout: :py:func:`~.pinout.assignment_count` assignments. The chosen
assignment is still validated in Vivado (see :py:mod:`.pinout`). The
jitx-pin-assignment skill covers the pattern (hierarchical provider
composition).
"""

from jitx.net import DiffPair, Net, Port, Provide

from ..js1_stackup_components.versal_fpga.circuit import XCVP1002Circuit
from .bundles import SLOT_BITS, VersalLPDDR4
from .pinout import LPDDR4_X32, Pos


class VP1002LPDDR4(XCVP1002Circuit):
    """JS1's VP1002 circuit plus the LPDDR4 offer and its system clock.

    ``sys_clk`` is the DDRMC's differential system clock input, on the
    fixed sys_clk pins of the layout. Net it to a clock source.

    ``IO_VR_700`` is bank 700's DCI reference pin, beside the GT calibration
    pins the base circuit exposes: it takes one external 240 ohm resistor to
    ``VCCO_700`` in every design (AMD AM010 v1.7, "Calibrated Termination";
    :py:class:`~.power.FpgaStraps`).
    """

    sys_clk = DiffPair()
    IO_VR_700 = Port()

    def __init__(self) -> None:
        super().__init__()
        layout = LPDDR4_X32
        self.SYS_CLK_P = self.sys_clk.p + self._pin(layout.fixed["SYS_CLK_P"])
        self.SYS_CLK_N = self.sys_clk.n + self._pin(layout.fixed["SYS_CLK_N"])
        self.IO_VR = Net([self.IO_VR_700, self.fpga.IO_VR_700], name="IO_VR_700")
        self.slot_bits = [
            Provide(bit).all_of(
                lambda b, slot=slot: [{b.p: self._pin(pos)} for pos in slot.dq]
            )
            for bit, slot in zip(SLOT_BITS, layout.slots, strict=True)
        ]
        self.lpddr4 = Provide(VersalLPDDR4).one_of(self._options)

    def _pin(self, pos: Pos) -> Port:
        """The VP1002 port at a position of triplet M0 (banks 700 to 702)."""
        return self.fpga.xpio_triplet_pins()[0][pos.index].port

    def _options(self, bus: VersalLPDDR4) -> list[dict[Port, Port]]:
        layout = LPDDR4_X32

        def at(name: str) -> Port:
            return self._pin(layout.fixed[name])

        fixed: dict[Port, Port] = {bus.reset_n: at("RESET_N")}
        for ch, c in zip(bus.ch, "AB", strict=True):
            fixed[ch.ck.p] = at(f"CK_T_{c}")
            fixed[ch.ck.n] = at(f"CK_C_{c}")
            fixed[ch.cke] = at(f"CKE_{c}")
            for rank, cs in enumerate(ch.cs):
                fixed[cs] = at(f"CS{rank}_{c}")
            for i, ca in enumerate(ch.ca):
                fixed[ca] = at(f"CA{i}_{c}")

        bits = [[b.p for b in self.require(bit, count=8)] for bit in SLOT_BITS]
        lanes = [lane for ch in bus.ch for lane in ch.d]  # bytes 0 to 3
        options: list[dict[Port, Port]] = []
        for order in layout.byte_orders():
            option = dict(fixed)
            for lane, slot_index in zip(lanes, order, strict=True):
                slot = layout.slots[slot_index]
                option[lane.dqs.p] = self._pin(slot.dqs_t)
                option[lane.dqs.n] = self._pin(slot.dqs_c)
                option[lane.dmi] = self._pin(slot.dmi)
                for dq, pin in zip(lane.dq, bits[slot_index], strict=True):
                    option[dq] = pin
            options.append(option)
        return options
