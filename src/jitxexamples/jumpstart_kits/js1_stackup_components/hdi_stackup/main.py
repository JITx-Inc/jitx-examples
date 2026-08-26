"""Test design — the minimum needed to prove the substrate builds.

The circuit is deliberately empty. Part 1's acceptance is a verified
*substrate*: that it type-checks, translates, and renders a correct
cross-section. Placing components, routing, and applying these routing
structures to real topologies is JS2 work, so nothing here reaches
for a parts query or a route.

What this design does prove: the 41-entry stackup translates, all 12 via
structures register off the substrate walk, all 19 fabrication constraints are
present, and the four routing structures resolve by impedance. The tests in
``tests/test_js1_hdi_stackup.py`` check each of those against the fab CSV.
"""

from jitx.circuit import Circuit
from jitx.design import Design

from .board import HDIBoard, HDISubstrate


class EmptyCircuit(Circuit):
    """No components — see the module docstring."""


class HDIStackupDesign(Design):
    """The 20-layer HDI substrate on its 80 x 80 mm board."""

    board = HDIBoard()
    substrate = HDISubstrate()
    circuit = EmptyCircuit()
