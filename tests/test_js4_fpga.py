"""JS4: the VP1002's LPDDR4X offer maps each signal to the pin the rules give it.

Reads the ``provide`` options back from an instantiated
:py:class:`~jitxexamples.jumpstart_kits.js4_fpga_lpddr4x.fpga.VP1002LPDDR4X`
and checks them against
:py:data:`~jitxexamples.jumpstart_kits.js4_fpga_lpddr4x.pinout.OPTIMUM_X32_FLIPPED`.
"""

from collections.abc import Mapping
from functools import cache

from jitx.net import Port
from jitx.si import ConstrainReferenceDifference, TimingDifferenceConstraint
from jitx.test import TestCase

from jitxexamples.jumpstart_kits.js4_fpga_lpddr4x.bundles import VersalLPDDR4X
from jitxexamples.jumpstart_kits.js4_fpga_lpddr4x.fpga import VP1002LPDDR4X
from jitxexamples.jumpstart_kits.js4_fpga_lpddr4x.main import JS4Circuit, JS4Design
from jitxexamples.jumpstart_kits.js4_fpga_lpddr4x.pinout import OPTIMUM_X32_FLIPPED, Pos
from jitxexamples.protocols.memory.lpddr4 import LPDDR4Lane

LAYOUT = OPTIMUM_X32_FLIPPED


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
        self.assertEqual(orders, set(LAYOUT.byte_orders()))

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


class TestNetFields(TestCase):
    def test_dq_is_indexed_byte_lane_then_bit(self) -> None:
        """DQ[2][5] is bit 5 of channel B's byte lane 0 on the memory side."""
        circuit = design().circuit
        assert isinstance(circuit, JS4Circuit)
        net = circuit.DQ[2][5]
        memory_bit = circuit.memory.lpddr4.ch[1].d[0].dq[5]
        self.assertEqual(len(net.connected), 2)
        self.assertTrue(any(port is memory_bit for port in net.connected))


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


class TestTimingConstraints(TestCase):
    """UG863 v1.12 Table 1, as :py:mod:`.constraint` applies it."""

    def references(self) -> list[ConstrainReferenceDifference]:
        circuit = design().circuit
        assert isinstance(circuit, JS4Circuit)
        return [
            c
            for c in circuit.lpddr4x_si.constrains
            if isinstance(c, ConstrainReferenceDifference)
        ]

    def test_no_dq_spread_rule(self) -> None:
        """UG863 has no DQ to DQ spread rule, so nothing is held against DMI."""
        circuit = design().circuit
        assert isinstance(circuit, JS4Circuit)
        dmi = {lane.dmi for ch in circuit.memory.lpddr4.ch for lane in ch.d}
        for c in self.references():
            self.assertNotIn(c.guide.end, dmi)

    def test_one_fpga_cke_held_to_both_balls(self) -> None:
        """Per channel, the FPGA's one CKE is held +/-20 ps from CK_T to each
        of the memory's two CKE balls."""
        circuit = design().circuit
        assert isinstance(circuit, JS4Circuit)
        for ch in circuit.memory.lpddr4.ch:
            starts: list[Port] = []
            for ball in ch.cke:
                found = [
                    (c, t)
                    for c in self.references()
                    if c.guide.end is ch.ck.p
                    for t in c.topologies
                    if t.end is ball
                ]
                self.assertEqual(len(found), 1)
                c, t = found[0]
                starts.append(t.begin)
                windows = {
                    (round(w.min_delta * 1e12, 3), round(w.max_delta * 1e12, 3))
                    for w in getattr(c, "_pairwise_constraints", [])
                    if isinstance(w, TimingDifferenceConstraint)
                }
                self.assertEqual(windows, {(-20.0, 20.0)})
            self.assertIs(starts[0], starts[1])
