"""The PUSB3FR4 ESD array as a provider of one protected differential pair.

Source: Nexperia, "PUSB3FR4 ESD protection for ultra high-speed interfaces",
Product data sheet, 12 July 2018,
https://assets.nexperia.com/documents/data-sheet/PUSB3FR4.pdf.

The channel freedom offered, and where the datasheet supports it:

- Which channel pair carries the signal: CH1 with CH2, or CH3 with CH4. The
  datasheet groups the channels that way as differential pairs: the graphic
  symbol of Table 1, Fig. 3 ("differential pairs CH1/CH2 versus CH3/CH4"),
  Fig. 4 (TDR of "differential pair CH1 + CH2") and the pass-through layout of
  Fig. 15. No other pairing is documented, so none is offered; CH2 with CH3
  would straddle the GND pin.
- Which channel of the pair carries P: either. The datasheet specifies every
  channel identically (Table 5: line capacitance 0.29 pF typical per channel,
  matching capacitance between signal pairs 0.05 pF maximum) and assigns no
  polarity to any channel.

For USB 2.0 "P" is D+ and "N" is D-: polarity is fixed end to end, so the
freedom is which ESD channel carries each line, never a P/N swap of the bus.

The layout is the datasheet's pass-through (Section 2, Fig. 15): each channel's
trace runs under the package across the channel pin and the n.c. pin opposite
it, so ``ProtectedPair`` nets every channel to that n.c. pin (CH1 with NC10,
CH2 with NC9, CH3 with NC7, CH4 with NC6). The protected signal stays on board
copper and needs no pin model.
"""

from jitx.circuit import Circuit
from jitx.net import DiffPair, Port, provide

from jitxexamples.components.digital_isolators.PUSB3FR4 import PUSB3FR4


class ProtectedPair(Circuit):
    """One PUSB3FR4 offering one differential pair on either documented channel
    pair, either way round."""

    gnd = Port()
    """Ground, both GND pins (3 and 8)."""

    def __init__(self) -> None:
        self.esd = PUSB3FR4()
        esd = self.esd
        self.gnd_net = self.gnd + esd.GND
        # Each channel runs on to an n.c. pin (datasheet Section 2, Fig. 15).
        self.CH1 = esd.CH1 + esd.NC10
        self.CH2 = esd.CH2 + esd.NC9
        self.CH3 = esd.CH3 + esd.NC7
        self.CH4 = esd.CH4 + esd.NC6

    @provide.one_of(DiffPair)
    def pair(self, dp: DiffPair) -> list[dict[Port, Port]]:
        """CH1/CH2 or CH3/CH4, either channel on P (see the module docstring)."""
        esd = self.esd
        return [
            {dp.p: esd.CH1, dp.n: esd.CH2},
            {dp.p: esd.CH2, dp.n: esd.CH1},
            {dp.p: esd.CH3, dp.n: esd.CH4},
            {dp.p: esd.CH4, dp.n: esd.CH3},
        ]
