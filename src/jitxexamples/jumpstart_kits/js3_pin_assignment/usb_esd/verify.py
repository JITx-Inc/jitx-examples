"""JS3 Part 2 verification designs: prove the USB constraint binds through the
pin-assigned ESD channels.

Each design wraps the shipping ``UsbEsdCircuit`` unchanged, places the USB parts
and closes both legs with code ``Route``s that end on the ESD array's physical
pads, so the routes pick one of the provider's mappings. These routes fix the
mapping, which is why they live here and never in ``main.py``.

- ``UsbEsdProof``: D+ on CH1, D- on CH2.
- ``UsbEsdProofSwapped``: the other channel pair with the polarity choice
  reversed, D+ on CH4 and D- on CH3.
- ``UsbEsdProofIllegal``: D+ on CH1, D- on CH3, a pairing the datasheet does not
  document and the provider does not offer. The runtime settles on one offered
  mapping and drops the routes that conflict with it.

The pass-through. Each leg also gets a route from its channel's land to the
n.c. land opposite (datasheet Fig. 15). The two lands share a net
(``esd.ProtectedPair``), and without copper between them the report says
"Unconnected Topology" at the ESD. They are separate ports of the PUSB3FR4
model on purpose: with one port mapped to both lands, the path end lands on
either of them from one run to the next, and the same design passes or fails at
random (jitx 4.6.0rc10, runtime 4.6.0-rc.16).

Geometry. The RP2040 has USB_DP to the left of USB_DM as the pair leaves the
package, and the receptacle has D+ (A6) to the right of D- (A7) as the pair
arrives, so the two legs must cross once. The D- leg crosses under D+ on the
bottom layer through two ``THVia_L1_L20``. JS1 gives its vias no SI models (see
its module docstring), so the report flags a placeholder model on that leg; the
measurement still appears.

Routing structure. ``DRS_100`` keeps 0.5944 mm clearance on the outer layers,
more than the gap beside a 0.4 mm pitch QFN pad or a 0.5 mm pitch DFN land, so
a route under it cannot reach these parts ("Unrealizable Route: Insufficient
space"). The proof routes therefore carry JS1's ``Neck_SE`` geometry (0.15 mm
line, 0.15 mm clearance) through a ``Route`` tag rule above the constraint's
structure. ``Neck_DIFF_100`` would fit too, but it has no uncoupled region, and
where the pair splits at the pads the report then says "Missing routing
structure". The neck geometry shortens the clearance, so these proofs show
binding, not that a ``DRS_100`` route fits: that is the board router's job,
with neck regions.
"""

from jitx.circuit import Circuit, Route
from jitx.constraints import Tag, Tags, design_constraint
from jitx.design import Design
from jitx.landpattern import Pad
from jitx.net import Net, Port
from jitx.via import Via

from jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup.board import (
    HDIBoard,
    HDISubstrate,
)

from .main import UsbEsdCircuit

# ESD channel -> (land on the RP2040 side, land on the connector side),
# from the PUSB3FR4 pad mapping: CH1 on 1 and 10, CH2 on 2 and 9, CH3 on 4
# and 7, CH4 on 5 and 6.
_LANDS: dict[str, tuple[int, int]] = {
    "CH1": (1, 10),
    "CH2": (2, 9),
    "CH3": (4, 7),
    "CH4": (5, 6),
}

# Placement, mm. The D+ leg runs straight up the column X_P from the RP2040's
# USB_DP pad (1.0, 3.4) to the receptacle's A6 contact.
X_P = 1.0
X_N_RES = 2.2  # D- series resistor column, right of D+
X_N_CONN = 0.0  # A7, left of D+
Y_RES = 5.5
Y_ESD = 9.5
Y_A_ROW = 14.0
A_ROW_OFFSET = 3.97  # Molex land pattern: A row at y = 3.97 from the origin
A6_OFFSET = 0.5  # A6 at x = -0.5, so +0.5 once turned 180 degrees


def _land_x(land: Pad) -> float:
    """A land's x offset from the ESD origin, unrotated."""
    assert land.transform is not None
    x, _ = land.transform * (0.0, 0.0)
    return x


class ProofNeck(Tag):
    """Proof routes, given JS1's ``Neck_SE`` geometry."""


class UsbEsdProofCircuit(Circuit):
    """``UsbEsdCircuit`` placed and code-routed with D+ on ``p_ch`` and D- on
    ``n_ch``."""

    def __init__(self, p_ch: str, n_ch: str) -> None:
        self.channels = (p_ch, n_ch)
        self.dut = UsbEsdCircuit()
        dut = self.dut
        mcu = dut.mcu
        esd = dut.esd.esd
        conn = dut.conn

        # Each leg enters the channel on its RP2040-side land, runs under the
        # package to the n.c. land opposite (the pass-through of datasheet
        # Fig. 15) and leaves from there. The land-to-land route matters: without
        # it the report says "Unconnected Topology" at the ESD.
        lands = esd.landpattern.p
        p_in, p_out = (lands[i] for i in _LANDS[p_ch])
        n_in, n_out = (lands[i] for i in _LANDS[n_ch])

        # D+ lands at X_P on the ESD.
        esd_x = X_P - _land_x(p_in)
        mcu.mcu.at(0.0, 0.0)
        mcu.r_usb_p.at(X_P, Y_RES, rotate=90)
        mcu.r_usb_n.at(X_N_RES, Y_RES, rotate=90)
        esd.at(esd_x, Y_ESD)
        conn.at(X_P - A6_OFFSET, Y_A_ROW + A_ROW_OFFSET, rotate=180)

        self.routes: list[Route] = [
            Route(mcu.mcu.USB.p, mcu.r_usb_p.p1, layer=0),
            Route(mcu.r_usb_p.p2, p_in, layer=0),
            Route(p_in, p_out, layer=0),
            Route(p_out, conn.D0.p, layer=0),
            Route(mcu.mcu.USB.n, mcu.r_usb_n.p1, layer=0),
            Route(n_in, n_out, layer=0),
        ]
        n_x = esd_x + _land_x(n_in)
        self.vias: list[Via] = []
        if n_x < X_P:
            # D- is already left of D+ at the ESD: cross before it.
            self.routes += self._cross(
                mcu.r_usb_n.p2, n_in, X_N_RES, min(n_x, X_P - 1.0), Y_RES + 1.5
            )
            self.routes.append(Route(n_out, conn.D0.n, layer=0))
        else:
            # D- is still right of D+ at the ESD: cross after it.
            self.routes.append(Route(mcu.r_usb_n.p2, n_in, layer=0))
            self.routes += self._cross(
                n_out, conn.D0.n, n_x + 0.7, X_N_CONN, Y_ESD + 1.5
            )

        for route in self.routes:
            Tags(ProofNeck()).assign(route)
        self.neck_rule = design_constraint(ProofNeck(), priority=1).routing_structure(
            HDISubstrate.Neck_SE, ref_net=dut.gnd
        )

    def _cross(
        self,
        start: Port | Pad,
        end: Port | Pad,
        x_right: float,
        x_left: float,
        y: float,
    ) -> list[Route]:
        """Take the D- leg from right of the D+ column to left of it, under D+ on
        the bottom layer."""
        right = HDISubstrate.THVia_L1_L20().at(x_right, y)
        left = HDISubstrate.THVia_L1_L20().at(x_left, y + 0.5)
        self.vias += [right, left]
        # Join the vias to D- here: a net in this circuit that names a D- pin
        # merges with the shipping circuit's USB_DM net, and this field keeps
        # its name.
        self.USB_DM = Net([self.dut.conn.D0.n, right, left])
        return [
            Route(start, right, layer=0),
            Route(right, left, layer=-1),
            Route(left, end, layer=0),
        ]


class UsbEsdProof(Design):
    """D+ on CH1, D- on CH2."""

    board = HDIBoard()
    substrate = HDISubstrate()

    def __init__(self) -> None:
        self.circuit = UsbEsdProofCircuit("CH1", "CH2")


class UsbEsdProofSwapped(Design):
    """D+ on CH4, D- on CH3."""

    board = HDIBoard()
    substrate = HDISubstrate()

    def __init__(self) -> None:
        self.circuit = UsbEsdProofCircuit("CH4", "CH3")


class UsbEsdProofIllegal(Design):
    """D+ on CH1, D- on CH3: not an offered mapping."""

    board = HDIBoard()
    substrate = HDISubstrate()

    def __init__(self) -> None:
        self.circuit = UsbEsdProofCircuit("CH1", "CH3")
