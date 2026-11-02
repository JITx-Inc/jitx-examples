"""
2012670005
"""

from typing import Iterable, override

from jitx.circuit import Circuit
from jitx.common import DualPair, Power
from jitx.component import Component
from jitx.landpattern import Landpattern, PadMapping
from jitx.net import DiffPair, Port, Provide, provide
from jitx.shapes import Shape
from jitx.shapes.composites import capsule, rectangle
from jitx.si import TerminatingPinModel
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitx.units import F, V, ohm
from jitxlib.landpatterns.courtyard import (
    CourtyardGeneratorMixin,
    ExcessCourtyardGenerator,
    OriginMarkerMixin,
)
from jitxlib.landpatterns.grid_layout import A1, AlphaDictNumberingBase, GridPosition
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import GridPadShapeGeneratorMixin, SMDPadConfig, THPad
from jitxlib.landpatterns.silkscreen.labels import ReferenceDesignatorMixin
from jitxlib.landpatterns.silkscreen.marker import Pad1Marker
from jitxlib.landpatterns.silkscreen.outlines import PackageBased, SilkscreenOutline
from jitxlib.parts import (
    AtLeast,
    Capacitor,
    CapacitorQuery,
    Minimize,
    Resistor,
    ResistorQuery,
)
from jitxlib.protocols.usb import USB2, USB_C_Connector
from jitxlib.symbols.box import BoxConfig, BoxSymbol, PinGroup, Row

# from jitxlib.diodes.ESD224DQAR import device as ESD224DQAR_device


class USBTypeCComponent(Component):
    """USB Type-C SMD Connectors ROHS"""

    manufacturer = "Molex"
    mpn = "2012670005"
    datasheet = "https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/201/201267/2012670005_sd.pdf"
    reference_designator_prefix = "J"

    GND = [Port() for _ in range(4)]
    VBUS = [Port() for _ in range(4)]
    TX1 = DiffPair()
    TX2 = DiffPair()
    RX1 = DiffPair()
    RX2 = DiffPair()
    D0 = DiffPair()
    D1 = DiffPair()
    CC1 = Port()
    CC2 = Port()
    SBU1 = Port()
    SBU2 = Port()
    SHIELD = Port()

    def __init__(self) -> None:
        self.landpattern = USBTypeCLandpattern()
        self.symbol_a = BoxSymbol(
            rows=[
                Row(
                    left=[],
                    right=[
                        PinGroup(self.VBUS[:2]),
                    ],
                ),
                Row(
                    left=[
                        PinGroup([self.D0.p, self.D0.n]),
                        PinGroup([self.TX1.p, self.TX1.n]),
                        PinGroup([self.RX1.p, self.RX1.n]),
                        PinGroup([self.CC1, self.SBU1]),
                    ],
                    right=[],
                ),
                Row(
                    left=[
                        PinGroup(self.GND[:2]),
                    ],
                    right=[
                        PinGroup([self.SHIELD]),
                    ],
                ),
            ],
            config=BoxConfig(
                group_spacing=2,
            ),
        )
        self.symbol_b = BoxSymbol(
            rows=[
                Row(
                    left=[],
                    right=[
                        PinGroup(self.VBUS[2:]),
                    ],
                ),
                Row(
                    left=[
                        PinGroup([self.D1.p, self.D1.n]),
                        PinGroup([self.TX2.p, self.TX2.n]),
                        PinGroup([self.RX2.p, self.RX2.n]),
                        PinGroup([self.CC2, self.SBU2]),
                    ],
                    right=[],
                ),
                Row(
                    left=[
                        PinGroup(self.GND[2:]),
                    ],
                    right=[],
                ),
            ],
            config=BoxConfig(
                group_spacing=2,
            ),
        )

        self.pad_mapping = PadMapping(
            {
                self.VBUS[0]: self.landpattern.A[4],
                self.VBUS[1]: self.landpattern.A[9],
                self.VBUS[3]: self.landpattern.B[4],
                self.VBUS[2]: self.landpattern.B[9],
                self.D0.p: self.landpattern.A[6],
                self.D0.n: self.landpattern.A[7],
                self.TX1.p: self.landpattern.A[2],
                self.TX1.n: self.landpattern.A[3],
                self.RX1.p: self.landpattern.B[11],
                self.RX1.n: self.landpattern.B[10],
                self.CC1: self.landpattern.A[5],
                self.SBU1: self.landpattern.A[8],
                self.D1.p: self.landpattern.B[6],
                self.D1.n: self.landpattern.B[7],
                self.TX2.p: self.landpattern.B[2],
                self.TX2.n: self.landpattern.B[3],
                self.RX2.p: self.landpattern.A[11],
                self.RX2.n: self.landpattern.A[10],
                self.CC2: self.landpattern.B[5],
                self.SBU2: self.landpattern.B[8],
                self.GND[0]: self.landpattern.A[1],
                self.GND[1]: self.landpattern.A[12],
                self.GND[2]: self.landpattern.B[12],
                self.GND[3]: self.landpattern.B[1],
                self.SHIELD: (
                    self.landpattern.M[1],
                    self.landpattern.M[2],
                    self.landpattern.M[3],
                    self.landpattern.M[4],
                ),
            }
        )

        self.pin_models = [
            TerminatingPinModel(self.D0.p, delay=0.0, loss=0.0),
            TerminatingPinModel(self.D0.n, delay=0.0, loss=0.0),
            TerminatingPinModel(self.D1.p, delay=0.0, loss=0.0),
            TerminatingPinModel(self.D1.n, delay=0.0, loss=0.0),
            TerminatingPinModel(self.TX1.p, delay=0.0, loss=0.0),
            TerminatingPinModel(self.TX1.n, delay=0.0, loss=0.0),
            TerminatingPinModel(self.TX2.p, delay=0.0, loss=0.0),
            TerminatingPinModel(self.TX2.n, delay=0.0, loss=0.0),
            TerminatingPinModel(self.RX1.p, delay=0.0, loss=0.0),
            TerminatingPinModel(self.RX1.n, delay=0.0, loss=0.0),
            TerminatingPinModel(self.RX2.p, delay=0.0, loss=0.0),
            TerminatingPinModel(self.RX2.n, delay=0.0, loss=0.0),
        ]

    @provide(DualPair)
    def provide_dual_pair(self, dual_pair: DualPair):
        return [
            {
                dual_pair.A.p: self.D0.p,
                dual_pair.A.n: self.D0.n,
                dual_pair.B.p: self.D1.p,
                dual_pair.B.n: self.D1.n,
            },
            {
                dual_pair.A.p: self.D1.p,
                dual_pair.A.n: self.D1.n,
                dual_pair.B.p: self.D0.p,
                dual_pair.B.n: self.D0.n,
            },
        ]


class USBTypeC(Circuit):
    conn = USB_C_Connector()
    J = USBTypeCComponent()

    def __init__(self) -> None:
        super().__init__()

        self.VBUS = sum(self.J.VBUS, start=self.conn.vbus.Vp)
        self.CC1 = self.J.CC1 + self.conn.bus.cc[0]
        self.CC2 = self.J.CC2 + self.conn.bus.cc[1]
        self.SBU1 = self.J.SBU1 + self.conn.bus.sbu[0]
        self.SBU2 = self.J.SBU2 + self.conn.bus.sbu[1]

        # Both D+/D- contact pairs (A6/A7, B6/B7) on the one USB 2.0 pair.
        require_usb = Provide.require(DualPair, self.J)
        self.D = self.conn.bus.data + require_usb.A + require_usb.B

        self.TX1 = self.J.TX1 + self.conn.bus.lane[0].TX
        self.TX2 = self.J.TX2 + self.conn.bus.lane[1].TX
        self.RX1 = self.J.RX1 + self.conn.bus.lane[0].RX
        self.RX2 = self.J.RX2 + self.conn.bus.lane[1].RX

        self.GND = sum(self.J.GND, start=self.conn.vbus.Vn)
        self.SHIELD = self.conn.shield + self.J.SHIELD


class USBC_HighSpeed_Iface(Circuit):
    """
    USB-C USB 2.0 High-Speed Interface

    This is a basic USB2 480mbps capable USB-C interface.
    It doesn't include the SuperSpeed connections, but does
    provide the necessary features to support a simple debug
    interface, like to an FTDI.

    Circuit Includes:
    1.  USB-C connector
    2.  Pull-downs for CC1 and CC2
    3.  Shield termination

    An SI constraint on the data pair names one pad at each end. ``USB``
    reaches both A6/A7 and B6/B7, so it has no single pad to measure to: end on
    the connector component's A6/A7 pair, ``USBC.J.D0``. Begin on the MCU
    component's own pins, not on a circuit port behind series parts, which
    would leave those parts out of the path.

    >>> class USBCircuit(Circuit):
    ...     usb = USBC_HighSpeed_Iface()
    ...     mcu = MCU()  # the MCU component, with a USB2 port named USB
    ...     usb_constraint = DiffPairConstraint(skew=USB.v2.skew, loss=USB.v2.loss)
    ...     def __init__(self):
    ...         self.usb_net = self.mcu.USB + self.usb.USB
    ...         self.usb_constraint.constrain(self.mcu.USB.data, self.usb.USBC.J.D0)
    """

    USB = USB2()
    VDD_USB = Power()
    USBC = USBTypeC()
    GND = Port()
    # esd_prot = ESD224DQAR_device()

    def __init__(self) -> None:
        rquery = ResistorQuery.require()
        cquery = CapacitorQuery.require()

        # VBUS is the supply legs only; both returns go on the ground below.
        self.VBUS = self.VDD_USB.Vp + self.USBC.conn.vbus.Vp

        self.pu_cc1 = Resistor(rquery, resistance=(5.1e3) * ohm)
        self.pu_cc2 = Resistor(rquery, resistance=(5.1e3) * ohm)
        self.CC1 = self.pu_cc1.p1 + self.USBC.conn.bus.cc[0]
        self.CC2 = self.pu_cc2.p1 + self.USBC.conn.bus.cc[1]

        self.usb_net = self.USB.data + self.USBC.conn.bus.data

        # Shield Termination
        voltage_filters = cquery.filters()
        if not ({"rated_voltage", "rated_voltage_dc"} & voltage_filters.keys()):
            cquery = cquery.update(
                rated_voltage_dc=AtLeast(50 * V), rank=Minimize("rated_voltage_dc")
            )
        self.sh_term_c = Capacitor(cquery, capacitance=(4.7e-9) * F)
        self.sh_term_r = Resistor(rquery, resistance=(0.0) * ohm)
        self.SHIELD = self.sh_term_c.p1 + self.sh_term_r.p1 + self.USBC.conn.shield

        # One ground: the port, both VBUS returns, the CC pull-downs and the
        # shield termination.
        self.gnd = (
            self.GND
            + self.VDD_USB.Vn
            + self.USBC.conn.vbus.Vn
            + self.pu_cc1.p2
            + self.pu_cc2.p2
            + self.sh_term_c.p2
            + self.sh_term_r.p2
        )


class USBTypeCLandpattern(
    A1,
    AlphaDictNumberingBase,
    SilkscreenOutline,
    Pad1Marker,
    ReferenceDesignatorMixin,
    CourtyardGeneratorMixin,
    OriginMarkerMixin,
    GridPadShapeGeneratorMixin,
    Landpattern,
):
    name = "USB Type C Connector"
    num_leads = 24
    A: dict[int, THPad]
    B: dict[int, THPad]
    M: dict[int, THPad]

    def __init__(self):
        super().__init__()
        self.package_body(
            RectanglePackage(
                width=Toleranced(9.39, 0.15),
                length=Toleranced.exact(8.3),
                height=Toleranced(3.71, 0.15),
            )
        )
        self.silkscreen_outline(PackageBased())
        self._num_rows = 2
        self._num_cols = 12

    def __base_init__(self):
        super().__base_init__()
        self.courtyard(ExcessCourtyardGenerator(0.25))
        self.pad_config(SMDPadConfig())

    @override
    def _pad_shape(self, pos: GridPosition) -> Shape:
        if pos.row == 1 and pos.column in [0, 11]:
            pad_width = 0.9
        else:
            pad_width = 0.3
        pad_height = 0.7
        return rectangle(pad_width, pad_height)

    @override
    def _generate_layout(self) -> Iterable[GridPosition]:
        # First row
        y0 = 3.97
        for c in range(12):
            x = -3.0 + 0.5 * c
            if c >= 6:
                x += 0.5
            yield GridPosition(0, c, Transform.translate(x, y0))
        # Second row
        y1 = 2.27
        for c in range(12):
            if c == 0:
                x = 3.05
            elif c == 11:
                x = -3.05
            else:
                x = 2.75 - 0.5 * c
            yield GridPosition(1, c, Transform.translate(x, y1))

    @override
    def _build(self) -> None:
        # wipe mutable fields
        self.A = {}
        self.B = {}
        self.M = {}
        super()._build()
        self.build_mounting_holes()

    def build_mounting_holes(self):
        copper12 = capsule(1.1, 2.1)
        cutout12 = capsule(0.6, 1.6)
        p1 = THPad(copper12, cutout12).at(-4.32, 3.16)
        p2 = THPad(copper12, cutout12).at(4.32, 3.16)

        copper34 = capsule(1.1, 3.6).at(0.0, 0.5)
        cutout34 = capsule(0.6, 2.1)
        p3 = THPad(copper34, cutout34).at(-4.62, -2.2)
        p4 = THPad(copper34, cutout34).at(4.62, -2.2)

        self.M = {
            1: p1,
            2: p2,
            3: p3,
            4: p4,
        }


Device: type[USBTypeC] = USBTypeC
