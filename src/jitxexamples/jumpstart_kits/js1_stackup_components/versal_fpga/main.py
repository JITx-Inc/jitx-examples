"""Buildable smoke designs for the VP1002 reference solution.

Two deliberately minimal ``SampleDesign``s:

* ``VersalFPGADesign`` — the bare component. One schematic page per
  generated ``BoxSymbol`` (one per bank / GT quad / rail chunk), which is
  how a ~1369-ball part stays reviewable. No routes, no substrate tuning:
  the point is that the component instantiates, maps every ball, and
  translates.
* ``VersalFPGACircuitDesign`` — the :class:`~.circuit.XCVP1002Circuit`
  wrapper (power rails, ground domains, GTM quad bundles) as consumed by a
  board design. Its boundary ports are left unconnected on purpose; the
  wrapper's internal nets are the design under test.

Build (runtime required)::

    jitx build jitxexamples.jumpstart_kits.js1_stackup_components.\\
versal_fpga.main.VersalFPGADesign
"""

from jitx import Circuit
from jitx.circuit import SchematicGroup
from jitx.container import inline
from jitx.sample import SampleDesign

from .circuit import XCVP1002Circuit
from .xcvp1002 import XCVP1002


class VersalFPGADesign(SampleDesign):
    """Bare XCVP1002 with one schematic page per symbol box."""

    @inline
    class circuit(Circuit):
        fpga = XCVP1002()

        def __init__(self):
            self.pages = [SchematicGroup(sym) for sym in self.fpga.symbols]


class VersalFPGACircuitDesign(SampleDesign):
    """The power/GTM circuit wrapper, instantiated as a board would."""

    @inline
    class circuit(Circuit):
        fpga_circuit = XCVP1002Circuit()
