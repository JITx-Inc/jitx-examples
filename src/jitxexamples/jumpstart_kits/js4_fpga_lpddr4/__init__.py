"""JS4 reference solution: the JS1 VP1002 driving a Micron LPDDR4 device, on
the 18-layer reference substrate
(:py:mod:`jitxexamples.substrates.reference_18layer`), taken through the
layout flow part by part.

- :py:mod:`.base`: the connected board every part starts from, with its
  rails' nets, calibration resistors and decoupling, only the FPGA placed,
  and no constraints or rules.
- :py:mod:`.ball_field`: the ball-field tag and the narrower structure a
  pair's route segment inside a ball field takes.
- :py:mod:`.reference_escapes`: where a reference layout of channel B's two
  byte lanes puts each strobe escape's insertion and pair point, the
  positions Part 1 places them at.
- :py:mod:`.part1_fanout_escape`: Part 1's reference, the base design with
  the memory placed, a via in the pad of every FPGA ball but its NC balls
  and every memory ball but NC and DNU, ground pours on the ground layers
  and channel B's two strobe pairs escaped from both parts' ball fields, each
  part's vias and routes in the part's own circuit so they move when that
  circuit moves. It leaves out of the decoupling the 27 capacitors that
  would connect to nothing on this board, never created.
- :py:mod:`.part2_power`: Part 2's reference, Part 1's design with the
  resistors and capacitors placed on BOTTOM in their parts' circuits, the
  small capacitors across ball vias and the rest in a ring outside each
  field, clear of the corridor Part 4's byte lanes take between the
  fields, every capacitor Part 1 keeps. It adds a pour for each of five rails on L9, L10 and L12, and
  the 2 oz layers' width and clearance floors.
- :py:mod:`.part3_si_constraints`: Part 3's reference, Part 2's design with
  UG863's timing, a loss limit, the package delay pin models and the
  spacing rules.
- :py:mod:`.part4_routing`: Part 4's reference, Part 3's design with
  every DQ, DMI and DQS of channel B's byte lanes 0 and 1 routed along a
  reference layout's paths (:py:mod:`.part4_reference_routes`), length
  matched by serpentines inside length-matching sections. The data lines
  carry no tag, and its control points sit only at the ends of those
  sections.
- :py:mod:`.constraint`: UG863's skew limits and trace length budget as a
  reusable constraint.
- :py:mod:`.models`: package delay pin models from a package delay file.
- :py:mod:`.rules`: UG863's spacing between the link's signal groups, with
  the under-device values on segments carrying the ball-field tag.

The FPGA's pin offer is a supplied part,
:py:mod:`jitxexamples.jumpstart_kits.vp1002_lpddr4`.
"""
