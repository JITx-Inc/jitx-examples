"""JS5 reference solution: a diplexer for 2.4 to 2.5 GHz and 5.1 to 5.9 GHz on
JLCPCB's 2-layer 0.76 mm RO4350B board: the board one run of the JS5 runbook
produced, with the jacks' in-pad vias left open where the run had them filled
and capped, a change no solve has scored.

- :py:mod:`.network`: the network, its eight 0402 parts from the
  ``jitxexamples`` catalogue and its three Würth edge-launch SMA jacks.
- :py:mod:`.main`: the board, placed, routed and poured in code.
- :py:mod:`.launch`: each jack's launch, shared geometry for the three.
- :py:mod:`.lines`: the 50 ohm line's structure, fence, stitching and rules.
- :py:mod:`.bodies`: the chip bodies the body keepouts are drawn from.
- :py:mod:`.substrate`: the JLCPCB substrate with the jacks' open in-pad via.

The run's HFSS setup, which needs the JITX Ansys library, is not part of this
package. ``fab/`` holds the fab notes and the JLCPCB packet exported from
:py:class:`.main.Diplexer`.
"""
