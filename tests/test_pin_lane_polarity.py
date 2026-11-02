"""Tests for the lane-choice and P/N-inversion pattern.

The jitx-pin-assignment skill points at ``jitxexamples.patterns.pin_lane_polarity``
for three shapes: a ``one_of`` provider offering either lane either way round,
a pass-through part carrying a ``BridgingPinModel`` per leg, and a constraint
whose Topology begins on the required pair. The tests read those from the
instantiated design, offline, and check that each verification design's routes
land on the serializer pins its name says: an offered mapping for the two
proofs, none for the illegal design. Whether the runtime measures them is in the
module docstring's pasted output.
"""

from __future__ import annotations

from jitx.circuit import Route
from jitx.inspect import extract
from jitx.net import DiffPair, Port, Provide
from jitx.si import BridgingPinModel, ConstrainDiffPair
from jitx.sample import SampleDesign
from jitx.test import TestCase

from jitxexamples.patterns.pin_lane_polarity import (
    LaneOneInvertedProof,
    LanePolarityDesign,
    LanePolarityLink,
    LanePolarityProof,
    LaneZeroProof,
    SplitLanesIllegal,
)


def _link() -> LanePolarityLink:
    circuit = LanePolarityDesign().circuit
    assert isinstance(circuit, LanePolarityLink)
    return circuit


def _option_pins(link: LanePolarityLink) -> set[tuple[int, int]]:
    """Each offered option as (id of the pin on ``p``, id of the pin on ``n``)."""
    (provide,) = extract(link.ser, Provide)
    bundle = provide.bundle
    assert isinstance(bundle, DiffPair)
    out: set[tuple[int, int]] = set()
    for option in provide.options:
        targets = {id(key): target for key, target in option}
        out.add((id(targets[id(bundle.p)]), id(targets[id(bundle.n)])))
    return out


def _expected_pins(link: LanePolarityLink) -> set[tuple[int, int]]:
    """Lane 0 and lane 1, each straight and inverted, written out by hand so a
    change to the module's ``OFFERED`` fails the test."""
    tx = link.ser.serializer.tx
    return {
        (id(tx[0].p), id(tx[0].n)),
        (id(tx[0].n), id(tx[0].p)),
        (id(tx[1].p), id(tx[1].n)),
        (id(tx[1].n), id(tx[1].p)),
    }


class TestLanePolarityShape(TestCase):
    def test_provider_offers_one_of_either_lane_either_way_round(self) -> None:
        link = _link()
        provides = list(extract(link.ser, Provide))
        self.assertEqual(len(provides), 1, "one one_of provide, not one per option")
        self.assertEqual(len(provides[0].options), 4)
        self.assertEqual(_option_pins(link), _expected_pins(link))

    def test_each_choke_winding_has_a_bridging_pin_model(self) -> None:
        choke = _link().choke
        ends = {
            tuple(id(p) for p in model.ports)
            for model in extract(choke, BridgingPinModel)
        }
        self.assertEqual(
            ends,
            {(id(choke.a_in), id(choke.a_out)), (id(choke.b_in), id(choke.b_out))},
        )

    def test_constraint_begins_on_the_required_pair(self) -> None:
        link = _link()
        constraint = link.link_constraint
        self.assertIsInstance(constraint, ConstrainDiffPair)
        (topology,) = constraint.topologies
        self.assertIs(topology.end, link.conn.rx)
        tx = link.ser.serializer.tx
        self.assertNotIn(id(topology.begin), {id(tx[0]), id(tx[1])})
        self.assertIsInstance(topology.begin, DiffPair)

    def test_shipping_design_has_no_routes_or_placement(self) -> None:
        link = _link()
        self.assertEqual(list(extract(link, Route)), [])
        for part in (link.ser.serializer, link.choke, link.conn):
            self.assertIsNone(part.transform)


class TestLanePolarityProofs(TestCase):
    def _routed_pins(self, proof: LanePolarityProof) -> tuple[int, int]:
        """Ids of the serializer pins routed to the choke's ``a_in`` and ``b_in``."""
        choke = proof.dut.choke
        by_end: dict[int, Port] = {}
        for route in proof.routes:
            ends = (route.source, route.destination)
            for here, there in (ends, ends[::-1]):
                if here is choke.a_in or here is choke.b_in:
                    assert isinstance(there, Port)
                    by_end[id(here)] = there
        return id(by_end[id(choke.a_in)]), id(by_end[id(choke.b_in)])

    def _proof(self, design: type[SampleDesign]) -> LanePolarityProof:
        circuit = design().circuit
        assert isinstance(circuit, LanePolarityProof)
        return circuit

    def test_every_part_is_placed(self) -> None:
        for design in (LaneZeroProof, LaneOneInvertedProof, SplitLanesIllegal):
            dut = self._proof(design).dut
            for part in (dut.ser.serializer, dut.choke, dut.conn):
                self.assertIsNotNone(part.transform, f"{design.__name__}: {part}")

    def test_proof_routes_match_an_offered_mapping_and_the_illegal_ones_do_not(
        self,
    ) -> None:
        for design, offered in (
            (LaneZeroProof, True),
            (LaneOneInvertedProof, True),
            (SplitLanesIllegal, False),
        ):
            proof = self._proof(design)
            pins = self._routed_pins(proof)
            self.assertEqual(
                pins in _expected_pins(proof.dut), offered, design.__name__
            )

    def test_inverted_proof_routes_lane_one_n_to_rx_p(self) -> None:
        proof = self._proof(LaneOneInvertedProof)
        tx = proof.dut.ser.serializer.tx
        self.assertEqual(self._routed_pins(proof), (id(tx[1].n), id(tx[1].p)))
