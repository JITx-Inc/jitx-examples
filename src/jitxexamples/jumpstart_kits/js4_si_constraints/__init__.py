"""JS4 reference solution: SI constraints on the JS1 VP1002 driving a Micron
LPDDR4X device.

- :py:mod:`.constraint`: UG863's skew limits and trace length budget as a
  reusable constraint.
- :py:mod:`.models`: package delay pin models from a package delay file,
  and microvia delay models from the stackup.
- :py:mod:`.main`: the shipping design, with no routes.
- :py:mod:`.proof`: code-routed verification designs that measure the
  constraints, before and after a tighter limit.

The FPGA's pin offer is a supplied part,
:py:mod:`jitxexamples.jumpstart_kits.vp1002_lpddr4x`.
"""
