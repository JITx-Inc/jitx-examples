"""JS2 reference solution: circuits composed through typed ports.

* :mod:`.straps` transcribes the KSZ9031RNX strap-in table into a typed
  configuration.
* :mod:`.phy` is the KSZ9031RNX application circuit, parametric in that
  configuration, with its 1.2 V core made by the PHY's on-chip LDO controller.
* :mod:`.main` composes a 3.3 V regulator, the PHY circuit and an RJ45 jack
  into one board design.
"""
