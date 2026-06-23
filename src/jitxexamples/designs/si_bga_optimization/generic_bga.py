"""Generic hex-grid BGA component used by the design.

Physical BGA properties (rows, cols, pitch, ball diameter, signal row
pairs) are canonical here, alongside the component definition itself.
Signal-pair lanes start one row above the bottom edge and repeat up
the row axis. Each lane uses adjacent P/N rows, and each deeper lane
shifts one column over. The row gaps alternate to compensate for the
hex column stagger.
"""

import math
from collections.abc import Iterable

import jitx
from jitx import PadMapping
from jitx.net import DiffPair, Port
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitxlib.landpatterns.generators.bga import BGADecorated
from jitxlib.landpatterns.grid_layout import (
    A1,
    AlphaDictNumbering,
    GridPosition,
)
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol, PinGroup, Row, Column


# -----------------------------------------------------------------------------
# BGA geometry constants and ball-position math.
# -----------------------------------------------------------------------------

BGA_ROWS = 21
BASE_BGA_COLS = 7
BGA_COLS = 8
BGA_LAYOUT_CENTER_COL = (BASE_BGA_COLS - 1) / 2.0
BGA_HPITCH = 1.0
BGA_VPITCH = BGA_HPITCH * math.sqrt(3.0) / 2.0
BGA_BALL_DIAMETER = 0.5

# One row pair per signal layer (Signal4..Signal1, deepest first). The
# innermost kept pair escapes to the deepest layer; ``signal_layer_for_pair``
# maps these four to Signal4/3/2/1 respectively, so each signal layer hosts
# exactly one fanout.
SIGNAL_ROW_PAIRS = ((11, 12), (13, 14), (16, 17), (18, 19))


def ball_center(row_index: int, col: int) -> tuple[float, float]:
    center_row = (BGA_ROWS - 1) / 2.0
    col_index = col - 1
    y_shift = -(BGA_HPITCH / 2.0) if (col_index % 2) else 0.0
    x = (col_index - BGA_LAYOUT_CENTER_COL) * BGA_VPITCH
    y = (center_row - row_index) * BGA_HPITCH + y_shift
    return x, y


def signal_cols_for_pair(pair_index: int) -> tuple[int, ...]:
    depth_from_bottom = len(SIGNAL_ROW_PAIRS) - 1 - pair_index
    return (2, 4, 6) if depth_from_bottom % 2 == 0 else (3, 5, 7)


def signal_layer_for_pair(pair_index: int) -> int:
    depth_from_bottom = len(SIGNAL_ROW_PAIRS) - 1 - pair_index
    return min(depth_from_bottom + 1, 4)


# -----------------------------------------------------------------------------
# Hex BGA landpattern.
# -----------------------------------------------------------------------------

_HEX_VPITCH_RATIO = math.sqrt(3) / 2  # ~= 0.866


def _num_gnd_balls() -> int:
    signal_balls = sum(
        2 * len(signal_cols_for_pair(i)) for i in range(len(SIGNAL_ROW_PAIRS))
    )
    return BGA_ROWS * BGA_COLS - signal_balls


class HexBGADecorated(BGADecorated):
    """BGA with alternate-column vertical offset for hex close-packed layout.

    Columns with odd index are shifted down by half the vertical pitch; column
    spacing is ``pitch * sqrt(3)/2``, so nearest-neighbor ball centers sit at
    exactly ``pitch`` in every direction.
    """

    def __init__(
        self,
        num_rows: int,
        num_cols: int,
        ball_diameter: float,
        pitch: float,
        center_col: float | None = None,
    ):
        super().__init__(num_rows, num_cols, ball_diameter, pitch)
        self._hex_hpitch = pitch
        self._hex_vpitch = pitch * _HEX_VPITCH_RATIO
        self._hex_center_col = center_col

    def _generate_layout(self) -> Iterable[GridPosition]:
        num_rows = self._num_rows
        num_cols = self._num_cols
        hpitch = self._hex_hpitch
        vpitch = self._hex_vpitch
        center_row = (num_rows - 1) / 2.0
        center_col = self._hex_center_col
        if center_col is None:
            center_col = (num_cols - 1) / 2.0
        for r in range(num_rows):
            for c in range(num_cols):
                y_shift = -(hpitch / 2.0) if (c % 2) else 0.0
                x = (c - center_col) * vpitch
                y = (center_row - r) * hpitch + y_shift
                yield GridPosition(r, c, Transform.translate(x, y))


class HexBGA(A1, AlphaDictNumbering, HexBGADecorated):
    """Hex-staggered BGA with A1-corner alpha/dict pad numbering."""

    def get_pad(self, r: int, c: int):
        """Public ``(row, col) -> Pad`` lookup.

        Polymorphic over the numbering mixin so design code stays
        decoupled from ``AlphaDictNumbering``'s row-letter attribute
        layout. Wraps the framework-internal ``_get_pad`` so callers
        can stay clear of leading-underscore access.
        """
        return self._get_pad(r, c)


# -----------------------------------------------------------------------------
# Component definition.
# -----------------------------------------------------------------------------


class GenericHexGridBGA(jitx.Component):
    """Hex-grid BGA exposing diff-pair lanes per signal row pair.

    ``lanes[pair_index][lane_index]`` is the ``DiffPair`` for a given
    signal row pair and column slot. The flat ordering of pairs is
    ``SIGNAL_ROW_PAIRS``; the column slots within a pair are
    ``signal_cols_for_pair(pair_index)``.
    """

    mpn = "GENERIC_BGA_3DP"
    manufacturer = "Generic"
    reference_designator_prefix = "U"

    lanes: list[list[DiffPair]] = [
        [DiffPair() for _ in signal_cols_for_pair(pair_index)]
        for pair_index in range(len(SIGNAL_ROW_PAIRS))
    ]

    GND = [Port() for _ in range(_num_gnd_balls())]

    landpattern = (
        HexBGA(
            num_rows=BGA_ROWS,
            num_cols=BGA_COLS,
            pitch=BGA_HPITCH,
            ball_diameter=BGA_BALL_DIAMETER,
            center_col=BGA_LAYOUT_CENTER_COL,
        )
        .pad_config(SMDPadConfig())
        .package_body(
            RectanglePackage(
                width=Toleranced.exact(8.5),
                length=Toleranced.exact(22.5),
                height=Toleranced.min_max(0.8, 1.0),
            )
        )
    )

    def __init__(self):
        lp = self.landpattern

        # Symbol: one row per signal row-pair, P legs on the left,
        # N legs on the right. GND balls hang off the bottom.
        self.symbol = BoxSymbol(
            rows=[
                Row(
                    left=PinGroup(dp.p for dp in pair_bundle),
                    right=PinGroup(dp.n for dp in pair_bundle),
                )
                for pair_bundle in self.lanes
            ],
            columns=Column(
                up=(),
                down=PinGroup(self.GND),
            ),
        )

        # Build the pad mapping structurally. Pad lookups go through
        # ``lp.get_pad(row, col)`` so design code stays decoupled from
        # the numbering scheme.
        mapping: dict = {}
        signal_balls: set[tuple[int, int]] = set()

        for pair_index, (top_row, bottom_row) in enumerate(SIGNAL_ROW_PAIRS):
            cols = signal_cols_for_pair(pair_index)
            for lane_index, col in enumerate(cols):
                pair = self.lanes[pair_index][lane_index]
                # bottom row -> P leg; top row -> N leg.
                mapping[pair.p] = [lp.get_pad(bottom_row, col)]
                mapping[pair.n] = [lp.get_pad(top_row, col)]
                signal_balls.add((bottom_row, col))
                signal_balls.add((top_row, col))

        gnd_iter = iter(self.GND)
        for row_index in range(BGA_ROWS):
            for col in range(1, BGA_COLS + 1):
                if (row_index, col) in signal_balls:
                    continue
                mapping[next(gnd_iter)] = [lp.get_pad(row_index, col)]

        self.mappings = [PadMapping(mapping)]
