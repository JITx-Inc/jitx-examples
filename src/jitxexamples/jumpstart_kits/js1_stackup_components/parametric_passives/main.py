from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitx.units import kohm

from .components.resistor import Resistor


class Resistors(Circuit):
    # Numeric values are interpreted as ohms; unit-bearing quantities also work.
    r1 = Resistor(resistance=100)
    r2 = Resistor(resistance=2 * kohm)
    nets = [r1.p1 + r2.p1, r1.p2 + r2.p2]


class ParametricPassives(SampleDesign):
    circuit = Resistors()
