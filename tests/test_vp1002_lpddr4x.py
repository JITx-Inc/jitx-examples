"""The VP1002's LPDDR4X offer maps each signal to the pin its layout gives it.

Reads the ``provide`` options back from an instantiated
:py:class:`~jitxexamples.jumpstart_kits.vp1002_lpddr4x.circuit.VP1002LPDDR4X`
and checks them against
:py:data:`~jitxexamples.jumpstart_kits.vp1002_lpddr4x.pinout.LPDDR4X_X32`.
"""

from collections.abc import Mapping
from functools import cache

from math import factorial

from jitx.net import Port
from jitx.test import TestCase

from jitxexamples.jumpstart_kits.js4_si_constraints.main import JS4Circuit, JS4Design
from jitxexamples.jumpstart_kits.vp1002_lpddr4x.bundles import VersalLPDDR4X
from jitxexamples.jumpstart_kits.vp1002_lpddr4x.circuit import VP1002LPDDR4X
from jitxexamples.jumpstart_kits.vp1002_lpddr4x.pinout import (
    LPDDR4X_X32,
    Pos,
    assignment_count,
)
from jitxexamples.protocols.memory.lpddr4 import LPDDR4Lane

LAYOUT = LPDDR4X_X32


@cache
def design() -> JS4Design:
    """One shared instantiation; call only inside a TestCase."""
    return JS4Design()


def fpga() -> VP1002LPDDR4X:
    circuit = design().circuit
    assert isinstance(circuit, JS4Circuit)
    return circuit.fpga


def pin(pos: Pos) -> Port:
    return fpga().fpga.xpio_triplet_pins()[0][pos.index].port


def bus() -> VersalLPDDR4X:
    bundle = fpga().lpddr4x.bundle
    assert isinstance(bundle, VersalLPDDR4X)
    return bundle


def options() -> list[Mapping[Port, Port]]:
    return [dict(option) for option in fpga().lpddr4x.options]


def lanes() -> list[LPDDR4Lane]:
    """Bytes 0 to 3, channel A then channel B."""
    return [lane for ch in bus().ch for lane in ch.d]


class TestFixedPins(TestCase):
    def test_every_option_maps_the_fixed_pins(self) -> None:
        b = bus()
        expected: dict[str, Port] = {"RESET_N": b.reset_n}
        for ch, c in zip(b.ch, "AB", strict=True):
            expected[f"CK_T_{c}"] = ch.ck.p
            expected[f"CK_C_{c}"] = ch.ck.n
            expected[f"CKE_{c}"] = ch.cke
            for rank, cs in enumerate(ch.cs):
                expected[f"CS{rank}_{c}"] = cs
            for i, ca in enumerate(ch.ca):
                expected[f"CA{i}_{c}"] = ca
        self.assertEqual(set(expected), set(LAYOUT.fixed) - {"SYS_CLK_P", "SYS_CLK_N"})
        for n, option in enumerate(options()):
            for name, port in expected.items():
                with self.subTest(option=n, signal=name):
                    self.assertIs(option[port], pin(LAYOUT.fixed[name]))


class TestByteSlots(TestCase):
    def test_options_are_the_allowed_byte_orders(self) -> None:
        orders: set[tuple[int, ...]] = set()
        for option in options():
            order: list[int] = []
            for lane in lanes():
                dqs_t = option[lane.dqs.p]
                found = [i for i, s in enumerate(LAYOUT.slots) if pin(s.dqs_t) is dqs_t]
                self.assertEqual(len(found), 1)
                order.append(found[0])
            orders.add(tuple(order))
        # PG313: a byte may swap only with the other byte of its own channel.
        # Slots 0 and 1 are channel A, 2 and 3 channel B; byte k defaults to
        # slot k.
        self.assertEqual(
            orders, {(0, 1, 2, 3), (1, 0, 2, 3), (0, 1, 3, 2), (1, 0, 3, 2)}
        )

    def test_dqs_and_dmi_go_with_their_slot(self) -> None:
        for n, (option, order) in enumerate(
            zip(options(), LAYOUT.byte_orders(), strict=True)
        ):
            for byte, (lane, slot_index) in enumerate(zip(lanes(), order, strict=True)):
                slot = LAYOUT.slots[slot_index]
                with self.subTest(option=n, byte=byte):
                    self.assertIs(option[lane.dqs.p], pin(slot.dqs_t))
                    self.assertIs(option[lane.dqs.n], pin(slot.dqs_c))
                    self.assertIs(option[lane.dmi], pin(slot.dmi))

    def test_dq_take_the_pins_of_their_slot(self) -> None:
        """A byte's eight DQ map to the eight bits required from its slot."""
        by_slot: dict[int, set[int]] = {}
        for n, (option, order) in enumerate(
            zip(options(), LAYOUT.byte_orders(), strict=True)
        ):
            for lane, slot_index in zip(lanes(), order, strict=True):
                bits = {id(option[dq]) for dq in lane.dq}
                with self.subTest(option=n, slot=slot_index):
                    self.assertEqual(len(bits), 8)
                    self.assertEqual(by_slot.setdefault(slot_index, bits), bits)
        self.assertEqual(len(by_slot), 4)
        self.assertEqual(len(set.union(*by_slot.values())), 32)


class TestSlotBits(TestCase):
    def test_each_slot_offers_its_eight_dq_pins(self) -> None:
        for slot_index, (offers, slot) in enumerate(
            zip(fpga().slot_bits, LAYOUT.slots, strict=True)
        ):
            offered: list[Port] = []
            for offer in offers:
                (option,) = offer.options
                ((bit, target),) = option
                self.assertIs(bit, offer.bundle.p)
                offered.append(target)
            with self.subTest(slot=slot_index):
                self.assertEqual(len(offered), 8)
                for target, pos in zip(offered, slot.dq, strict=True):
                    self.assertIs(target, pin(pos))


class TestLayout(TestCase):
    def test_assignment_count(self) -> None:
        """PG313's two swaps on one x32 layout: each channel's two bytes in
        either slot order (2 * 2), and any order of each byte's eight DQ."""
        self.assertEqual(assignment_count(), 2 * 2 * factorial(8) ** 4)

    def test_layout_uses_banks_702_and_701(self) -> None:
        """The flipped single channel layout sits on the third and second
        banks of the triplet: VP1002 banks 702 and 701."""
        positions = [*LAYOUT.fixed.values()]
        for slot in LAYOUT.slots:
            positions += [slot.dqs_t, slot.dqs_c, slot.dmi, *slot.dq]
        self.assertEqual({p.bank for p in positions}, {1, 2})
        self.assertEqual(len(set(positions)), len(positions))
