"""The diplexer network: three edge-launch SMA jacks (Würth 60312202114514),
two LQW15A inductors and six Accu-P capacitors.

Element order is the approved rough path's; values stay in its part families.
From the junction (J1 centre):

- LOW arm: L1 series to node A; branch C3 at A; L2 series to node B; branch C4
  at B; node B is J2's centre.
- HIGH arm: C1 series to node C; branch C5 at C; C2 series to node D; branch C6
  at D; node D is J3's centre.

Branch lines
------------
Each branch is a 0.20 mm printed line from its arm node to the hot pad of its
tip capacitor, whose other pad goes to ground. The line is copper, not a part,
so electrically it is a conductor of the arm node: the hot pad sits on the arm
node's own net (``NODE_A``, ``LOW``, ``NODE_C``, ``HIGH``). The layout draws
the line as a code ``Route`` on that net, from a ``RoutePoint`` on the arm
line to the branch capacitor's ``p1``, tagged for its 0.20 mm width
(``jitx-code-layout``). Each branch capacitor is its own field
(``c3`` to ``c6``), and its ``p1`` is the stub tip, so the layout names the
line's end structurally.

A separate stub-tip net joined to the arm node would need an
``OverlappableCopper`` net tie and a ``VirtualConnection``; the router ignores
overlappable copper, so the line could not be a routed trace under the
width and clearance rules, and the netlist would carry a short to explain.

Parts
-----
Every passive is a ``jitxlib.parts`` query against the ``jitxexamples``
catalogue (``jitxexamples/parts/example-passives.csv``). At every value used
here the catalogue holds two Accu-P grades (P, +/-0.02 pF; Z, +/-0.01 pF) and
a Murata GJM C0G part. The approved parts are Z grade, so each capacitor filters on
manufacturer, the ``thin_film`` type and a relative tolerance no looser than
+/-0.01 pF at its value: the CSV ``tolerance`` column is relative, so the
bound is 0.01 pF over the capacitance. The inductors filter on Murata's
``rf_wirewound`` type at G grade (+/-2 %).
"""

from jitx.circuit import Circuit
from jitx.net import Net, Port
from jitx.units import nH, pF
from jitxexamples.components.connectors.wurth_elektronik_60312202114514 import (
    Wurth60312202114514,
)
from jitxlib.parts import AtMost, Capacitor, CapacitorQuery, Inductor, InductorQuery

ACCU_P = CapacitorQuery(manufacturer="Kyocera AVX", case="0402", type="thin_film")
"""Kyocera AVX Accu-P 0402 thin-film capacitors (the approved part family)."""

ACCU_P_Z_GRADE_PF = 0.01
"""Accu-P tolerance code Z: +/-0.01 pF (Kyocera AVX Accu-P data sheet (https://datasheets.kyocera-avx.com/accu-p.pdf),
How to Order)."""

LQW15A = InductorQuery(manufacturer="Murata", case="0402", type="rf_wirewound")
"""Murata LQW15A 0402 wire-wound RF inductors (the approved part family)."""

LQW15A_G_GRADE = 0.02
"""LQW15A tolerance code G: +/-2 % (Murata LQW15AN_80 reference specification JELF243A-0100)."""


def accu_p_z(capacitance_pf: float) -> Capacitor:
    """An Accu-P 0402 capacitor of ``capacitance_pf`` picofarads at Z grade."""
    return Capacitor(
        ACCU_P,
        capacitance=capacitance_pf * pF,
        tolerance=AtMost(ACCU_P_Z_GRADE_PF / capacitance_pf),
    )


def lqw15a_g(inductance_nh: float) -> Inductor:
    """An LQW15A 0402 inductor of ``inductance_nh`` nanohenries at G grade."""
    return Inductor(
        LQW15A, inductance=inductance_nh * nH, tolerance=AtMost(LQW15A_G_GRADE)
    )


class Diplexer(Circuit):
    """The whole network with its three jacks. ``gnd`` is the ground return the
    top-level design names and pours."""

    gnd = Port()

    def __init__(self) -> None:
        self.j1 = Wurth60312202114514()
        """COMMON jack."""
        self.j2 = Wurth60312202114514()
        """LOW jack."""
        self.j3 = Wurth60312202114514()
        """HIGH jack."""

        # Low-pass arm: series inductors.
        self.l1 = lqw15a_g(3.7)
        self.l2 = lqw15a_g(3.5)
        # High-pass arm: series capacitors.
        self.c1 = accu_p_z(0.4)
        self.c2 = accu_p_z(1.3)
        # Branch tip capacitors (RF resonator elements, not decoupling).
        self.c3 = accu_p_z(0.9)
        self.c4 = accu_p_z(0.2)
        # The run's campaign tuned C5 at 1.7 pF; the user adopted 1.6 pF
        # (04021J1R6ZBSTR), re-closed on its final solve with the copper unchanged.
        self.c5 = accu_p_z(1.6)
        self.c6 = accu_p_z(0.8)

        self.COMMON = Net([self.j1.sig, self.l1.p1, self.c1.p1])
        self.NODE_A = Net([self.l1.p2, self.l2.p1, self.c3.p1])
        self.LOW = Net([self.l2.p2, self.c4.p1, self.j2.sig])
        self.NODE_C = Net([self.c1.p2, self.c2.p1, self.c5.p1])
        self.HIGH = Net([self.c2.p2, self.c6.p1, self.j3.sig])
        self.GND = Net(
            [
                self.gnd,
                self.j1.gnd,
                self.j2.gnd,
                self.j3.gnd,
                self.c3.p2,
                self.c4.p2,
                self.c5.p2,
                self.c6.p2,
            ]
        )
