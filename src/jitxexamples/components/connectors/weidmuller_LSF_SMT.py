"""
LSF-SMT PCB Terminal Blocks
===========================

Component definitions for Weidmüller LSF-SMT PCB terminal blocks.
"""

from typing import override

from jitx.component import Component
from jitx.landpattern import Pad, PadMapping
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitxlib.landpatterns.courtyard import (
    CourtyardGeneratorMixin,
    ExcessCourtyardGenerator,
)
from jitxlib.landpatterns.grid_layout import (
    A1,
    GridLayoutInterface,
    GridPosition,
    LinearNumbering,
)
from jitxlib.landpatterns.package import PackageBodyMixin, RectanglePackage
from jitxlib.landpatterns.pads import THPad, compute_hole_and_pad_diameters
from jitxlib.landpatterns.silkscreen.labels import ReferenceDesignatorMixin
from jitxlib.landpatterns.silkscreen.outlines import PackageBased, SilkscreenOutline
from jitxlib.symbols.box import BoxSymbol


# This file only contains the 3.5mm 180 degree variant
# TODO: Add variable pitch and 90 degree variants
LSF_SMT_PITCH = 3.5
LSF_SMT_VERTICAL_PITCH = 5.5


# Pulled from https://eshop.weidmueller.com/en/lsf-smt-3-5180/c/group21472460020482
# TU used when available, otherwise RL
poles_to_mpn = [
    "1446220000",
    "1825640000",
    "1825650000",
    "1825660000",
    "1825670000",
    "1825680000",
    "1825690000",
    "1825700000",
    "1825710000",
    "1825720000",
    "1825730000",
    "1825740000",
    "1870350000",
    "1870360000",
    "1870370000",
    "1870510000",
    "1870520000",
    "1870540000",
    "1870560000",
    "1870570000",
    "1870600000",
    "1870610000",
    "1870620000",
    "1870630000",
]
max_poles = len(poles_to_mpn)


class LSF_SMT(Component):
    """LSF-SMT PCB terminal block"""

    p: dict[int, Port]
    """Ports of the terminal block, indexed by pole number starting at 1."""

    class Landpattern(
        SilkscreenOutline,
        ReferenceDesignatorMixin,
        CourtyardGeneratorMixin,
        PackageBodyMixin,
        A1,
        LinearNumbering,
        GridLayoutInterface,
    ):
        """LSF-SMT terminal block landpattern."""

        def __init__(self, num_poles: int):
            super().__init__()
            self._num_rows = num_poles
            self._num_cols = 2
            self.hole_diam, self.pad_diam = compute_hole_and_pad_diameters(
                Toleranced(1.2, 0.0, 0.1), self._density_level
            )
            # THPadConfig does not do well with the rectangle pad at the moment.
            # self.pad_config(IPCTHPadConfig())
            self.package_body(self.make_package_body(num_poles))
            self.courtyard(ExcessCourtyardGenerator(0.25))
            self.silkscreen_outline(PackageBased().silkscreen_corner())

        @override
        def _generate_layout(self):
            y = LSF_SMT_VERTICAL_PITCH / 2
            for i in range(self._num_rows):
                c = (self._num_rows - 1) / 2
                pitch = LSF_SMT_PITCH
                x = (i - c) * pitch
                yield GridPosition(
                    row=i,
                    column=0,
                    pose=Transform.translate(x, y),
                )
                yield GridPosition(row=i, column=1, pose=Transform.translate(x, -y))

        # If we use a pad config, we can change this to a _pad_shape override.
        @override
        def _create_pad(self, pos: GridPosition) -> Pad:
            r, c = pos.row, pos.column
            if r == c == 0:
                return THPad(
                    copper=rectangle(self.pad_diam, self.pad_diam),
                    cutout=Circle(diameter=self.hole_diam),
                ).at(pos.pose)
            else:
                return THPad(
                    copper=Circle(diameter=self.pad_diam),
                    cutout=Circle(diameter=self.hole_diam),
                ).at(pos.pose)

        @classmethod
        def package_body_width(cls, num_poles: int) -> Toleranced:
            return Toleranced((num_poles - 1) * LSF_SMT_PITCH + 4.2, 0.15)

        @classmethod
        def make_package_body(cls, num_poles: int):
            pkg = RectanglePackage(
                length=Toleranced(8.5, 0.0),
                width=cls.package_body_width(num_poles),
                height=Toleranced(14.0, 0.0),
            )
            pkg.transform = Transform.translate(0.0, -0.1)
            return pkg

    def __init__(self, num_poles: int) -> None:
        if num_poles < 1 or num_poles > max_poles:
            raise ValueError(
                f"Terminal block with pole count '{num_poles}' not supported - must be within [1, {max_poles}]"
            )

        self.name = f"Terminal Block {num_poles} Poles"
        self.description = f"TERM BLK {num_poles}P TOP ENTRY 3.5MM PCB"
        self.manufacturer = "Weidmüller"
        self.mpn = poles_to_mpn[num_poles - 1]
        self.datasheet = (
            "https://eshop.weidmueller.com/en/lsf-smt-3-5180/c/group21472460020482"
        )
        self.reference_designator_prefix = "J"

        self.p = {(i + 1): Port() for i in range(num_poles)}

        self.landpattern = self.Landpattern(num_poles=num_poles)
        self.symbol = BoxSymbol()

        self.pad_mapping = PadMapping(
            (
                self.p[i + 1],
                (self.landpattern.p[2 * i + 1], self.landpattern.p[2 * i + 2]),
            )
            for i in range(num_poles)
        )


Device: type[LSF_SMT] = LSF_SMT
