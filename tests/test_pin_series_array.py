"""Tests for the pass-through channel pattern.

The jitx-pin-assignment skill points at ``jitxexamples.patterns.pin_series_array``
for a bundle that covers both sides of a pass-through part, so one offered
mapping sets the pin on each side of a channel together. The tests read the
instantiated design offline: one ``all_of`` option per array channel with both
sides set, a ``BridgingPinModel`` per channel, constraints on fixed physical
ends, and verification routes that keep each bit on one channel (swapped proof)
or change channel inside the part (illegal design). Whether the runtime measures
them is in the module docstring's pasted output.
"""

from __future__ import annotations

from jitx.circuit import Route
from jitx.inspect import extract
from jitx.net import Port, Provide
from jitx.si import BridgingPinModel, Constrain, ConstrainReferenceDifference
from jitx.sample import SampleDesign
from jitx.test import TestCase

from jitxexamples.patterns.pin_series_array import (
    ArrayChannel,
    SeriesArrayBus,
    SeriesArrayDesign,
    SeriesArrayProof,
    SidesDisagreeIllegal,
    SwappedChannelsProof,
)


def _bus() -> SeriesArrayBus:
    circuit = SeriesArrayDesign().circuit
    assert isinstance(circuit, SeriesArrayBus)
    return circuit


def _proof(design: type[SampleDesign]) -> SeriesArrayProof:
    circuit = design().circuit
    assert isinstance(circuit, SeriesArrayProof)
    return circuit


def _channel_of(ports: list[Port], target: Port) -> int:
    (index,) = [i for i, port in enumerate(ports) if port is target]
    return index


class TestSeriesArrayShape(TestCase):
    def test_one_all_of_option_per_channel_setting_both_sides(self) -> None:
        bus = _bus()
        array = bus.term.array
        provides = list(extract(bus.term, Provide))
        # all_of: one provide per mapping, each with a single option.
        self.assertEqual([len(p.options) for p in provides], [1, 1, 1, 1])
        offered: set[tuple[int, int]] = set()
        for provide in provides:
            bundle = provide.bundle
            assert isinstance(bundle, ArrayChannel)
            (option,) = provide.options
            targets = {id(key): target for key, target in option}
            self.assertEqual(set(targets), {id(bundle.a), id(bundle.b)})
            a = _channel_of(array.a, targets[id(bundle.a)])
            b = _channel_of(array.b, targets[id(bundle.b)])
            offered.add((a, b))
        self.assertEqual(offered, {(0, 0), (1, 1), (2, 2), (3, 3)})

    def test_each_channel_has_a_bridging_pin_model(self) -> None:
        array = _bus().term.array
        ends = {
            tuple(id(p) for p in model.ports)
            for model in extract(array, BridgingPinModel)
        }
        self.assertEqual(ends, {(id(array.a[i]), id(array.b[i])) for i in range(4)})

    def test_constraints_sit_on_fixed_physical_ends(self) -> None:
        bus = _bus()
        self.assertEqual(len(bus.bit_constraints), 4)
        for i, constraint in enumerate(bus.bit_constraints):
            self.assertIsInstance(constraint, Constrain)
            (topology,) = constraint.topologies
            self.assertIs(topology.begin, bus.drv.d[i])
            self.assertIs(topology.end, bus.rcv.d[i])
        skew = bus.bus_skew
        self.assertIsInstance(skew, ConstrainReferenceDifference)
        self.assertIs(skew.guide.begin, bus.drv.d[0])
        self.assertEqual(
            [id(t.begin) for t in skew.topologies],
            [id(bus.drv.d[i]) for i in (1, 2, 3)],
        )

    def test_shipping_design_has_no_routes_or_placement(self) -> None:
        bus = _bus()
        self.assertEqual(list(extract(bus, Route)), [])
        for part in (bus.drv, bus.rcv, bus.term.array):
            self.assertIsNone(part.transform)


class TestSeriesArrayProofs(TestCase):
    def _channels(self, proof: SeriesArrayProof) -> list[tuple[int, int]]:
        """(channel entered, channel left) for each bit, from the routes."""
        dut = proof.dut
        array = dut.term.array
        entered: dict[int, int] = {}
        left: dict[int, int] = {}
        for route in proof.routes:
            ends = (route.source, route.destination)
            for here, there in (ends, ends[::-1]):
                for i in range(4):
                    if here is dut.drv.d[i]:
                        assert isinstance(there, Port)
                        entered[i] = _channel_of(array.a, there)
                    if here is dut.rcv.d[i]:
                        assert isinstance(there, Port)
                        left[i] = _channel_of(array.b, there)
        return [(entered[i], left[i]) for i in range(4)]

    def test_every_part_is_placed(self) -> None:
        for design in (SwappedChannelsProof, SidesDisagreeIllegal):
            dut = _proof(design).dut
            for part in (dut.drv, dut.rcv, dut.term.array):
                self.assertIsNotNone(part.transform, f"{design.__name__}: {part}")

    def test_swapped_proof_keeps_each_bit_on_one_channel(self) -> None:
        self.assertEqual(
            self._channels(_proof(SwappedChannelsProof)),
            [(1, 1), (0, 0), (2, 2), (3, 3)],
        )

    def test_illegal_design_changes_channel_inside_the_part(self) -> None:
        self.assertEqual(
            self._channels(_proof(SidesDisagreeIllegal)),
            [(1, 0), (0, 1), (2, 2), (3, 3)],
        )
