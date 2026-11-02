"""JS4 reference solution: the JS1 VP1002 driving a Micron LPDDR4X device.

- :py:mod:`.pinout`: AMD's LPDDR4/4X pin rules for one DDRMC triplet, with
  their sources, as data.
- :py:mod:`.bundles`: the controller-side LPDDR4X bundle and the per-slot
  DQ bit ports the offer is built from.
- :py:mod:`.fpga`: the JS1 VP1002 circuit with those rules offered as
  ``provide`` options on banks 702 and 701.
- :py:mod:`.constraint`: UG863 timing limits on the link.
- :py:mod:`.main`: the shipping design, with no routes.
- :py:mod:`.proof`: the code-routed verification designs, one legal
  assignment and one illegal.
"""
