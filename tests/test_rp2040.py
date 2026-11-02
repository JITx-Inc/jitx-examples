# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point. The jitxcore._proto
# types below are private too, used only to annotate the translated design.
from jitx._translate.design import package_design
from jitx import current
from jitx.container import inline
from jitx.si import DiffPairConstraint
from jitx.test import TestCase
from jitx.circuit import Circuit
from tests.parts import PartsTestDesign
from jitxlib.parts import CapacitorQuery, ResistorQuery
from jitxlib.protocols.serial import I2C, SPI, UART
from jitxlib.protocols.usb import USB
from jitxcore._proto.design_pb2 import DesignV1
from jitxcore._proto.module_pb2 import Module
from jitxcore._proto.ports_pb2 import PortType

from jitxexamples.components.connectors import molex_2012670005
from jitxexamples.components.mcus import raspberry_pi_RP2040


class RP2040Design(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        mcu = raspberry_pi_RP2040.RP2040()

        def __init__(self):
            i1 = self.mcu.require(I2C)
            i2 = self.mcu.require(I2C)
            self.net = i1 + i2
            s1 = self.mcu.require(SPI(cs=True))
            s2 = self.mcu.require(SPI(cs=True))
            self.snet = s1 + s2

            # Test UART loopback - require two UART interfaces and connect them
            u1 = self.mcu.require(UART)
            u2 = self.mcu.require(UART)
            assert u1.rx and u1.tx
            assert u2.rx and u2.tx
            self.uart_loopback_nets = [
                u1.tx + u2.rx,  # Connect UART1 TX to UART2 RX
                u1.rx + u2.tx,  # Connect UART1 RX to UART2 TX
            ]

            self.usb = molex_2012670005.USBC_HighSpeed_Iface()

            self.usb_constraint = DiffPairConstraint(
                USB.v2.skew,
                USB.v2.loss,
                current.substrate.differential_routing_structure(100.0),
            )
            self.usb_net = self.mcu.usb + self.usb.USB
            # One pad pair at each end: the RP2040's own USB pins, ahead of the
            # 27 ohm series resistors, and the connector's A6/A7 contacts.
            # `self.usb.USB` reaches both A6/A7 and B6/B7, so it has no single
            # pad to measure to.
            self.usb_constraint.constrain(self.mcu.mcu.USB, self.usb.USBC.J.D0)


Node = tuple[int, ...]


class _Wiring:
    """Electrical nets of a translated design, flattened through its hierarchy.

    A node is a path from the top module: instance ids, then a port and its
    bundle sub-ports. A net between bundles joins them leaf by leaf. Pin
    assignment is resolved here only for ``DualPair`` requires, using mapping
    ``option`` of those the component provides (each ``provide`` option is its
    own support); other requires are left unjoined.
    """

    def __init__(self, v1: DesignV1, option: int) -> None:
        self.modules = {m.id: m for m in v1.modules}
        self.bundles = {b.id: b for b in v1.bundles}
        self.components = {c.id: c for c in v1.components}
        self.parent: dict[Node, Node] = {}
        self.option = option
        self._walk(self.modules[v1.module], ())

    def _leaves(self, port_type: PortType) -> list[Node]:
        if not port_type.HasField("bundle"):
            return [()]
        ports = self.bundles[port_type.bundle.bundle].ports
        return [(p.id, *leaf) for p in ports for leaf in self._leaves(p.type)]

    def _find(self, node: Node) -> Node:
        while self.parent.get(node, node) != node:
            node = self.parent[node]
        return node

    def _union(self, a: Node, b: Node) -> None:
        self.parent[self._find(a)] = self._find(b)

    def joined(self, a: Node, b: Node) -> bool:
        return self._find(a) == self._find(b)

    def _walk(self, module: Module, prefix: Node) -> None:
        net_ids = {n.id for n in module.nets}
        for net in module.nets:
            for leaf in self._leaves(net.type):
                here = (*prefix, -net.id, *leaf)
                for ref in net.refs:
                    path = tuple(ref.path)
                    if len(path) == 1 and path[0] in net_ids:
                        self._union(here, (*prefix, -path[0], *leaf))
                    else:
                        self._union(here, (*prefix, *path, *leaf))
        instances = {i.id: i for i in module.instances}
        for req in module.requires:
            bundle = req.port.type.bundle.bundle
            if self.bundles[bundle].name != "DualPair":
                continue
            (target,) = req.instance.path
            component = self.components[instances[target].instantiable]
            choices = [
                o for s in component.supports if s.bundle == bundle for o in s.options
            ]
            for entry in choices[self.option].entries:
                self._union(
                    (*prefix, req.port.id, *entry.key.path[1:]),
                    (*prefix, target, *entry.value.path),
                )
        for inst in module.instances:
            if inst.instantiable in self.modules:
                self._walk(self.modules[inst.instantiable], (*prefix, inst.id))


class TestRP2040(TestCase):
    def test_rp2040(self):
        design = RP2040Design()
        self.assertIsInstance(design.circuit.mcu, raspberry_pi_RP2040.RP2040)

    def test_usb_pins_reach_connector_a6_a7(self):
        """Each USB data leg runs from the RP2040's series resistor to the
        connector's A6/A7 pad under either DualPair assignment, and the SI
        constraint ends on the RP2040 pins and on D0 (A6/A7)."""
        v1 = package_design(RP2040Design()).v1
        modules = {m.id: m for m in v1.modules}
        components = {c.id: c for c in v1.components}
        bundles = {b.id: b for b in v1.bundles}

        def child(parent: int, name: str) -> tuple[int, int]:
            (inst,) = [i for i in modules[parent].instances if i.name == name]
            return inst.id, inst.instantiable

        def leg(component: int, port: str, sub: str | None = None) -> Node:
            (p,) = [p for p in components[component].ports if p.name == port]
            if sub is None:
                return (p.id,)
            (s,) = [s for s in bundles[p.type.bundle.bundle].ports if s.name == sub]
            return (p.id, s.id)

        mcu, rp2040 = child(v1.module, "mcu")
        chip_id, chip = child(rp2040, "mcu")
        usb, iface = child(v1.module, "usb")
        usbc, typec = child(iface, "USBC")
        j_id, j = child(typec, "J")
        pads = {
            tuple(e.key.path): e.value.path[-1]
            for e in components[j].landpattern_map.entries
        }
        (landpattern,) = [
            lp for lp in v1.landpatterns if lp.id == components[j].landpattern_map.id
        ]
        pad_names = {pad.id: pad.ref for pad in landpattern.pads}
        options = sum(
            len(s.options)
            for s in components[j].supports
            if bundles[s.bundle].name == "DualPair"
        )
        self.assertEqual(options, 2)

        wirings = [_Wiring(v1, option) for option in range(options)]
        loss_p, loss_n = modules[v1.module].constrain_insertion_losses
        other = {"p": "n", "n": "p"}
        for sub, pad, loss in (("p", "A[6]", loss_p), ("n", "A[7]", loss_n)):
            # The net starts at the series resistor's far pin: the resistor
            # (not a net) joins it to the RP2040 pin the constraint begins on.
            resistor_id, resistor = child(rp2040, f"r_usb_{sub}")
            near = (mcu, resistor_id, *leg(resistor, "p2"))
            far = (usb, usbc, j_id, *leg(j, "D0", sub))
            self.assertEqual(pad_names[pads[leg(j, "D0", sub)]], pad)
            self.assertEqual(
                (tuple(loss.path.key.path), tuple(loss.path.value.path)),
                ((mcu, chip_id, *leg(chip, "USB", sub)), far),
            )
            other_far = (usb, usbc, j_id, *leg(j, "D0", other[sub]))
            for option, wiring in enumerate(wirings):
                with self.subTest(leg=sub, option=option):
                    self.assertTrue(wiring.joined(near, far))
                    self.assertFalse(wiring.joined(near, other_far))
