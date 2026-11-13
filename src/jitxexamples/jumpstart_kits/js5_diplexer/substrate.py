"""The diplexer board's substrate.

JLCPCB's two-layer 0.762 mm RO4350B buildup from ``jitxlib.jlcpcb``, with one
via added: the open in-pad ground via the edge-launch jacks take
(:py:mod:`.launch`). JLCPCB neither fills nor caps vias on its Rogers boards,
so ``JLC02076_RO4350B`` offers no via-in-pad via; this one is its preferred
standard via, allowed in a pad and left untented, which the fab notes say.
"""

from jitxlib.jlcpcb import JLC02076_RO4350B


class DiplexerSubstrate(JLC02076_RO4350B):
    """``JLC02076_RO4350B`` with the jacks' open in-pad ground via."""

    class InPadVia(JLC02076_RO4350B.StdViaPreferred):
        """``StdViaPreferred`` (0.45 mm pad, 0.30 mm drill) placed in a solder
        pad: plated, not filled, capped or tented."""

        name = "Standard Via in Pad, Open - No Extra Cost"
        tented = False
        via_in_pad = True
