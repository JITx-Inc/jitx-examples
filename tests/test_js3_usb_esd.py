"""JS3 Part 2: the PUSB3FR4 provider offers exactly the channel freedom the
datasheet documents, and the proof designs route offered and unoffered
mappings as their names say. Offline: no runtime needed."""

from jitx.circuit import Route
from jitx.inspect import extract
from jitx.landpattern import Pad
from jitx.net import DiffPair, Port, Provide
from jitx.test import TestCase

from jitxexamples.jumpstart_kits.js3_pin_assignment.usb_esd.esd import ProtectedPair
from jitxexamples.jumpstart_kits.js3_pin_assignment.usb_esd.main import (
    UsbEsdCircuit,
    UsbEsdDesign,
)
from jitxexamples.jumpstart_kits.js3_pin_assignment.usb_esd.verify import (
    UsbEsdProof,
    UsbEsdProofIllegal,
    UsbEsdProofSwapped,
    UsbEsdProofCircuit,
)

# PUSB3FR4 datasheet, 12 July 2018: pairs CH1/CH2 and CH3/CH4 (Table 1 symbol,
# Figs. 3, 4 and 15), either channel of a pair on D+ (Table 5).
DOCUMENTED = {("CH1", "CH2"), ("CH2", "CH1"), ("CH3", "CH4"), ("CH4", "CH3")}
CHANNELS = ("CH1", "CH2", "CH3", "CH4")


def _offered(pair: ProtectedPair) -> set[tuple[str, str]]:
    """(P channel, N channel) for every option of the pair's DiffPair provide."""
    names = {id(getattr(pair.esd, ch)): ch for ch in CHANNELS}
    (provide,) = [p for p in extract(pair, Provide) if isinstance(p.bundle, DiffPair)]
    out: set[tuple[str, str]] = set()
    for option in provide.options:
        m: dict[int, Port] = {id(b): t for b, t in option}
        out.add(
            (names[id(m[id(provide.bundle.p)])], names[id(m[id(provide.bundle.n)])])
        )
    return out


def _pads(pair: ProtectedPair, port: Port) -> set[int]:
    """ids of the lands the PUSB3FR4's PadMapping gives ``port``."""
    for mapped, pads in pair.esd.mappings[0].items():
        if mapped is port:
            assert isinstance(pads, (Pad, list, tuple))
            return {id(pads)} if isinstance(pads, Pad) else {id(p) for p in pads}
    raise AssertionError("port not in the PUSB3FR4 pad mapping")


def _channel_lands(pair: ProtectedPair, channel: str) -> frozenset[int]:
    """The channel's land and the land of the n.c. pin netted to it."""
    port = getattr(pair.esd, channel)
    channels = [pair.CH1, pair.CH2, pair.CH3, pair.CH4]
    (net,) = [n for n in channels if any(m is port for m in n.connected)]
    lands: set[int] = set()
    for member in net.connected:
        assert isinstance(member, Port)
        lands |= _pads(pair, member)
    return frozenset(lands)


def _ends(route: Route, lands: set[int]) -> set[int]:
    """ids of the route's ends that are among ``lands``."""
    return {id(route.source), id(route.destination)} & lands


def _first_lands(routes: list[Route], start: object, lands: set[int]) -> set[int]:
    """ids of the lands first reached by following routes from ``start``."""
    seen = {id(start)}
    frontier = [start]
    reached: set[int] = set()
    while frontier:
        node = frontier.pop()
        for route in routes:
            ends = (route.source, route.destination)
            if not any(node is end for end in ends):
                continue
            for end in ends:
                if id(end) in seen:
                    continue
                seen.add(id(end))
                if id(end) in lands:
                    reached.add(id(end))
                else:
                    frontier.append(end)
    return reached


def _circuit() -> UsbEsdCircuit:
    circuit = UsbEsdDesign().circuit
    assert isinstance(circuit, UsbEsdCircuit)
    return circuit


class TestJS3UsbEsd(TestCase):
    def test_provider_offers_the_documented_mappings(self) -> None:
        self.assertEqual(_offered(_circuit().esd), DOCUMENTED)

    def test_every_channel_is_netted_to_its_pass_through_pin(self) -> None:
        circuit = _circuit()
        esd = circuit.esd.esd
        # Datasheet Section 2 and Fig. 15: CH1 runs on to pin 10, CH2 to 9,
        # CH3 to 7, CH4 to 6.
        expected = [
            {id(esd.CH1), id(esd.NC10)},
            {id(esd.CH2), id(esd.NC9)},
            {id(esd.CH3), id(esd.NC7)},
            {id(esd.CH4), id(esd.NC6)},
        ]
        pair = circuit.esd
        channels = [pair.CH1, pair.CH2, pair.CH3, pair.CH4]
        got = [{id(p) for p in net.connected} for net in channels]
        self.assertEqual(got, expected)

    def test_proof_variants_match_their_claims(self) -> None:
        cases = {
            UsbEsdProof: (("CH1", "CH2"), True),
            UsbEsdProofSwapped: (("CH4", "CH3"), True),
            UsbEsdProofIllegal: (("CH1", "CH3"), False),
        }
        for design_type, (channels, offered) in cases.items():
            circuit = design_type().circuit
            assert isinstance(circuit, UsbEsdProofCircuit)
            self.assertEqual(circuit.channels, channels)
            self.assertEqual(channels in DOCUMENTED, offered, design_type.__name__)

    def test_proof_routes_land_on_the_named_channels(self) -> None:
        for design_type in (UsbEsdProof, UsbEsdProofSwapped, UsbEsdProofIllegal):
            circuit = design_type().circuit
            assert isinstance(circuit, UsbEsdProofCircuit)
            pair = circuit.dut.esd
            p_ch, n_ch = circuit.channels
            all_lands = {id(pad) for pad in pair.esd.landpattern.p.values()}

            # Land to land: each leg runs from its channel's land to the n.c.
            # land opposite, as the PUSB3FR4 pad mapping and pass-through say.
            land_to_land = {
                frozenset(_ends(r, all_lands))
                for r in circuit.routes
                if len(_ends(r, all_lands)) == 2
            }
            self.assertEqual(
                land_to_land,
                {_channel_lands(pair, p_ch), _channel_lands(pair, n_ch)},
                design_type.__name__,
            )
            # D+ enters the ESD on the named P channel's own land.
            r_p2 = circuit.dut.mcu.r_usb_p.p2
            (entry,) = [
                r for r in circuit.routes if r_p2 is r.source or r_p2 is r.destination
            ]
            self.assertEqual(
                _ends(entry, all_lands),
                _pads(pair, getattr(pair.esd, p_ch)),
                design_type.__name__,
            )
            # D- enters the ESD on the named N channel's own land, possibly
            # through the crossing's vias.
            self.assertEqual(
                _first_lands(circuit.routes, circuit.dut.mcu.r_usb_n.p2, all_lands),
                _pads(pair, getattr(pair.esd, n_ch)),
                design_type.__name__,
            )
