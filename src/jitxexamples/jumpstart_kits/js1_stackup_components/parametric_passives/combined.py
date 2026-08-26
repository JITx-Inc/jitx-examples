"""Combined showcase design: one part from each of the four parametric families.

This is the runbook's final verification design (step 8) plus its live
part-request example (step 9): a 49.9 kOhm 0402 +/-1% Yageo and a 100 nF X7R
0603 50 V Samsung CL, alongside a Panasonic ERJ and a Vishay CRCW. Building
this design proves all four family classes generate valid land patterns,
symbols, and part numbers side by side.
"""

from jitx.circuit import Circuit
from jitx.sample import SampleDesign

from .components.panasonic_erj import PanasonicERJ
from .components.samsung_cl import SamsungCL
from .components.vishay_crcw import VishayCRCW
from .components.yageo_rc import YageoRC


class FourFamilies(Circuit):
    # The runbook's live part request: 49.9 kOhm 0402 1% Yageo (E96 value)
    # and a 100 nF X7R 0603 50 V Samsung CL (live catalog part).
    r_yageo = YageoRC(resistance=49_900, size="0402", tolerance=0.01)
    c_samsung = SamsungCL(capacitance=100e-9, size="0603")
    # One part from each remaining family.
    r_panasonic = PanasonicERJ(resistance=1000, size="0603")
    r_vishay = VishayCRCW(resistance=562, size="0603", tolerance=0.01)

    nets = [
        r_yageo.p1 + r_panasonic.p1 + r_vishay.p1 + c_samsung.p1,
        r_yageo.p2 + r_panasonic.p2 + r_vishay.p2 + c_samsung.p2,
    ]


class ParametricPassivesShowcase(SampleDesign):
    circuit = FourFamilies()
