"""JS1 Part 3 reference solution — AMD Versal Premium VP1002 FPGA (NFVI1369).

A 1369-ball BGA component generated from the AMD package pinout file
(``tools/generate_pinout.py``), plus the circuit wrapper that exposes its
power rails, ground domains, and GTM transceiver quads as a JITX-native
boundary.
"""

from .circuit import XCVP1002Circuit
from .xcvp1002 import XCVP1002

__all__ = ["XCVP1002", "XCVP1002Circuit"]
