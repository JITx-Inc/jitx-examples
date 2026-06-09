"""
XUNPU Tactile Switch TS-1088-AR02016
====================================

Component definition for XUNPU TS-1088-AR02016 tactile switch.
This is a surface-mount tactile switch with 4.0mm x 2.9mm body size.

Usage:

>>> from jitxexamples.components.buttons.xunpu_TS_1088_AR02016 import TS_1088_AR02016 as TactileSwitch
>>> class MyCircuit(Circuit):
...     def __init__(self):
...         self.button = TactileSwitch()
...         # Connect switch terminals
...         self.nets = [
...             self.button.p[1] + some_signal,
...             self.button.p[2] + another_signal
...         ]
"""

from jitx.anchor import Anchor
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.component import Component


class RectangleSmdPad(Pad):
    """SMD pad definition for the tactile switch terminals.

    Rectangular pad with dimensions 1.53mm x 1.36mm, with appropriate
    solder mask and paste stencil openings for reliable soldering.
    """

    shape = rectangle(1.53, 1.36)
    soldermask = Soldermask(rectangle(1.632, 1.462))
    paste = Paste(rectangle(1.632, 1.462))


class LandpatternSW_SMD_L4_0_W2_9_LS5_0(Landpattern):
    """PCB landpattern for XUNPU TS-1088-AR02016 tactile switch.

    Surface-mount landpattern with 4.0mm x 2.9mm body size and 5.0mm lead span.
    Features two rectangular SMD pads positioned at ±2.035mm from center.
    Includes silkscreen outline, courtyard boundary, and 3D model reference.
    """

    name = "SW-SMD_L4.0-W2.9-LS5.0"
    p = {
        1: RectangleSmdPad().at((-2.035, -0.0005)),
        2: RectangleSmdPad().at((2.035, -0.0005)),
    }
    reference_designator = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 3.3581)))
    value_label = Custom(Text(">VALUE", 0.5, Anchor.W).at((-0.75, 2.3581)), name="Fab")
    silkscreen = [
        Silkscreen(Polyline(0.152, [(2.076, 1.5765), (-2.076, 1.5765)])),
        Silkscreen(Polyline(0.152, [(2.076, -1.5765), (2.076, -0.8835)])),
        Silkscreen(Polyline(0.152, [(2.076, 1.5765), (2.076, 0.8835)])),
        Silkscreen(Polyline(0.152, [(-2.076, 1.5765), (-2.076, 0.8835)])),
        Silkscreen(Polyline(0.152, [(2.076, -1.5765), (-2.076, -1.5765)])),
        Silkscreen(Polyline(0.152, [(-2.076, -1.5765), (-2.076, -0.8835)])),
        Silkscreen(ArcPolyline(0.254, [Arc((0, -0.0005), 0.813, 0, -360)])),
    ]
    custom_layer = [
        Custom(ArcPolyline(0.06, [Arc((-2.5, -1.4505), 0.03, 0, -360)]), name="Fab")
    ]
    courtyard = Courtyard(rectangle(5.702, 3.305))
    model = Model3D(
        "xunpu_TS_1088_AR02016.stp",
        position=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
        rotation=(0.0, 0.0, 0.0),
    )


class SymbolTS_1088_AR02016(Symbol):
    """Schematic symbol for XUNPU TS-1088-AR02016 tactile switch.

    Two-terminal switch symbol with standard tactile switch representation.
    Pin 1 on the left, Pin 2 on the right, with visual switch actuator indication.
    """

    pin_name_size = 0.7874
    pad_name_size = 0.7874
    p = {1: Pin((-4, 0), 2, Direction.Left), 2: Pin((4, 0), 2, Direction.Right)}
    layer_reference = Text(">REF", 0.55559, Anchor.C).at((0, 2.97481))
    layer_value = Text(">VALUE", 0.55559, Anchor.C).at((0, 2.1874))
    draws = [
        Circle(radius=0.4).at((1.6, 0)),
        Circle(radius=0.4).at((-1.6, 0)),
        Polyline(0.254, [(-1.8, 0.4), (1.6, 1.4)]),
        Polyline(0.254, [(4.00001, 0), (2, 0)]),
        Polyline(0.254, [(-4.00001, 0), (-2, 0)]),
    ]


class TS_1088_AR02016(Component):
    """XUNPU TS-1088-AR02016 tactile switch component.

    Surface-mount tactile switch with momentary normally-open contacts.
    Suitable for user interface applications requiring tactile feedback.

    Specifications:
    - Body size: 4.0mm x 2.9mm
    - Lead span: 5.0mm
    - Operating force: Typically 160gf
    - Contact resistance: <100mΩ
    - Operating temperature: -40°C to +85°C

    Ports:
    - p[1]: Switch terminal 1
    - p[2]: Switch terminal 2

    Note: Switch terminals are electrically equivalent - either can be used
    as input or output depending on circuit requirements.
    """

    manufacturer = "XUNPU"
    mpn = "TS-1088-AR02016"
    reference_designator_prefix = "S"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_XUNPU-TS-1088-AR02016_C720477.pdf"
    p = {1: Port(), 2: Port()}
    landpattern = LandpatternSW_SMD_L4_0_W2_9_LS5_0()
    symbol = SymbolTS_1088_AR02016()
    cmappings = [
        SymbolMapping({p[1]: symbol.p[1], p[2]: symbol.p[2]}),
        PadMapping({p[1]: landpattern.p[1], p[2]: landpattern.p[2]}),
    ]


Device: type[TS_1088_AR02016] = TS_1088_AR02016
