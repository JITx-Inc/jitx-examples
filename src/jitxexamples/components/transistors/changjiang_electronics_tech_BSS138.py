"""
DEPRECATED: This file is deprecated and maintained only for backwards compatibility.

Please use the canonical BSS138 definition from:
    from jitxexamples.components.fets_n_ch.BSS138 import BSS138

The BSS138 is a standard part number available from multiple manufacturers
(LGE, Changjiang Electronics Tech, ON Semiconductor, etc.). All use the same
SOT-23-3 package and have similar electrical characteristics.

This file previously defined a Changjiang Electronics Tech (CJ) specific version,
but we now use a single canonical definition with standard SOT-23-3 landpattern.
"""

# Re-export the canonical BSS138 component for backwards compatibility
from ..fets_n_ch.BSS138 import BSS138, Device

__all__ = ["BSS138", "Device"]
