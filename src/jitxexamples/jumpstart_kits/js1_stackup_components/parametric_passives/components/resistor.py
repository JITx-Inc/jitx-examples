"""Generic parametric 0402 resistor component.

This local model uses JITX's standard resistor symbol and 0402 landpattern. It
does not select or claim a manufacturer part number.
"""

from jitx.component import Component
from jitx.net import Port
from jitx.units import PlainQuantity, ohm
from jitxlib.landpatterns.twopin.smt import SMT
from jitxlib.symbols.resistor import ResistorSymbol


class Resistor(Component):
    """A generic 0402 resistor parameterized by resistance.

    A numeric resistance is interpreted as ohms. A JITX quantity with compatible
    resistance units, such as ``2 * kohm``, is kept in its supplied unit. Zero
    ohms is valid for components used as electrical jumpers.
    """

    p1 = Port()
    p2 = Port()
    landpattern = SMT("0402")
    symbol = ResistorSymbol()
    reference_designator_prefix = "R"

    resistance: PlainQuantity

    def __init__(self, *, resistance: float | PlainQuantity):
        if isinstance(resistance, PlainQuantity):
            ohm.m_from(resistance, name="resistance")
        else:
            resistance = ohm.from_(resistance, strict=False, name="resistance")

        if resistance.magnitude < 0:
            raise ValueError("resistance must not be negative")

        self.resistance = resistance
        self.value = resistance
