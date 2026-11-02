"""JS1 Part 2 reference solution: AMD Versal Premium VP1002 FPGA (NFVI1369).

A 1369-ball BGA component generated from the AMD package pinout file
(``tools/generate_pinout.py``), plus the circuit wrapper that exposes its
power rails, ground domains, and GTM transceiver quads as a JITX-native
boundary.

The two names below are re-exported lazily (PEP 562). Both submodules they come
from import ``jitx``, and this package sits on the import path of
``python -m ...versal_fpga.tools.generate_pinout`` -- so an eager re-export makes
the documented command fail with ``ModuleNotFoundError`` unless jitx is
installed. The generator is deliberately stdlib-only precisely so it can
run without a jitx environment; ``TestGenerator.test_runs_without_jitx`` seals
that. Keep these lazy.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .circuit import XCVP1002Circuit
    from .xcvp1002 import XCVP1002

__all__ = ["XCVP1002", "XCVP1002Circuit"]


def __dir__() -> list[str]:
    # PEP 562: the lazy names are absent from the module __dict__ until first
    # accessed, so without this they vanish from dir() and tab-completion.
    # Union rather than __all__ alone, which would also drop the module globals
    # and the already-imported submodules that eager re-exports left visible.
    return sorted({*globals(), *__all__})


def __getattr__(name: str) -> type:
    if name == "XCVP1002":
        from .xcvp1002 import XCVP1002

        return XCVP1002
    if name == "XCVP1002Circuit":
        from .circuit import XCVP1002Circuit

        return XCVP1002Circuit
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
