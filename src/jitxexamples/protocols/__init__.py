"""
High-speed protocol bundles and signal-integrity constraints
============================================================

Each module in this package defines a protocol's port bundles and a
:py:class:`~jitx.si.SignalConstraint` that applies the protocol's timing, skew
and loss limits, with the numbers' sources cited in the module docstring. Each
protocol has a worked example design beside it, named ``<protocol>_example``.

Protocols that ``jitxlib.protocols`` already ships (USB, Ethernet,
DisplayPort, RGMII and others) are not repeated here. Of the protocols in
``JITx-Inc/jitx-protocols-ext``, PCIe, SFP, JESD204, SATA, DDR5, LPDDR5 and
GDDR7 were left out: none came with both a real part and spec-cited numbers
to implement it fully.

How the constraints attach (jitx 4.6)
-------------------------------------

The constraints are written for jitx 4.6 and use no ``>>`` topology:

- Connect the two ends with ordinary nets (``a + b``, or ``Net([...])``), then
  call the constraint's ``constrain(src, dst)``. It applies
  :py:class:`~jitx.si.Constrain`, :py:class:`~jitx.si.ConstrainDiffPair` and
  :py:class:`~jitx.si.ConstrainReferenceDifference` to
  ``Topology(begin, end)`` for each signal.
- The path between the two ends is inferred, and inference needs routes.
  Before the board is routed the design-issue report carries no measurement,
  only unrouted-path messages (``Unconnected Topology``). Code ``Route``\\ s
  close the path without the board view. The example designs are not
  routed; to see measurements, route the board on your own stackup, in the
  board view or with code routes.
- Keep each constrained net between component pins. On jitx 4.6 an unrouted
  path that crosses a circuit's port reports ``No path for signal
  constraint`` rather than ``Unconnected Topology``; it measures once routed.
- A part the signal passes through (a series resistor, an AC coupling
  capacitor) needs a :py:class:`~jitx.si.BridgingPinModel` between its two
  ports, or the path stops at that part and the issue report names it.
- Package delay counts only where a part's pins carry a
  :py:class:`~jitx.si.TerminatingPinModel`. The memory modules say which
  side's package their sources want included.
- Check the constraints from Python, with the project's runtime running::

      import jitx

      from mypackage.main import MyDesign


      def main() -> None:
          with jitx.runtime as rt:
              report = rt.submit(MyDesign).issues(satisfied=True, wait=30)
              if not report.complete:
                  print("report incomplete: raise wait and run again")
              for group in report.groups():
                  print("met" if group.satisfied else "NOT MET", group.text)
                  if len(group.issues) > 1:
                      for issue in group:
                          print("   ", issue.text)


      if __name__ == "__main__":
          main()

  Without ``satisfied=True`` a constraint that is met is not reported. A
  group of several issues shows only the first in its text, so the loop
  prints the rest; ``report.complete`` is false when the wait ran out before
  every check finished. A constraint has applied only when its group carries a
  measurement,
  and it is met only when ``group.satisfied`` is true. A constraint that sets
  only a routing structure has no group of its own.
- ``ConstrainReferenceDifference(guide, target)`` checks guide delay minus
  target delay against the window you pass. The report prints the window
  with its sign dropped: windows of -1000 ps to 0 and 0 to 1000 ps both
  print as ``Target: 500ps ± 500ps``. The printed
  target does not say which way the window points, so read pass or fail
  from ``group.satisfied``.
- ``>>`` (``TopologyNet``) is for a daisy chain whose order is part of the
  design, such as a fly-by clock. None of the examples here is a daisy chain.
"""
