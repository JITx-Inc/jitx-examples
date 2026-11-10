"""The JS1 VP1002 with one LPDDR4X x32 interface offered on banks 702 and 701.

A supplied part for JumpStart Kit 4: the FPGA offers every byte swap and bit
swap AMD's LPDDR4/4X pin rules allow on one layout, and JITX picks the
assignment when the board is routed. A design requires
:py:class:`.bundles.VersalLPDDR4X` from :py:class:`.circuit.VP1002LPDDR4X`
and nets it to the memory.

- :py:mod:`.pinout`: the layout and its sources, as data.
- :py:mod:`.bundles`: the controller-side bundle and the per-slot DQ ports.
- :py:mod:`.circuit`: the VP1002 circuit with the offer.
- :py:mod:`.package_delays`: a package delay file for the offer's pins, in
  the shape of Vivado's I/O ports export, holding synthetic estimates, not
  AMD data.
"""
