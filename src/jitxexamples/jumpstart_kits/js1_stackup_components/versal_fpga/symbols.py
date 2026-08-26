"""Symbol partitioning and pad-mapping helpers for the VP1002 component.

The generated component (:mod:`.xcvp1002`) stays declarative: it yields
``SymbolPartition`` records and ``(port, (row, col))`` ball assignments; the
two builders here turn those into jitxlib ``BoxSymbol`` instances and a
``PadMapping``. Keeping the builders handwritten (and tiny) means the
generated file contains data-shaped code only.

Ports are never *stored* in extra containers on the component — a ``Port``
may have only one home in the design tree (JITX raises "encountered
multiple times" otherwise). Partitions are therefore exposed as a method
that yields fresh records; tests assert symbol coverage by re-calling it.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from jitx import PadMapping
from jitx.landpattern import Pad
from jitx.net import Port
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row

from .landpattern import VersalBGA

#: Readability cap — no symbol box gets more pins than this.
MAX_PINS_PER_BOX = 64


@dataclass(frozen=True)
class SymbolPartition:
    """Ports of one schematic box: left/right rows, optional bottom column."""

    left: tuple[Port, ...] = ()
    right: tuple[Port, ...] = ()
    down: tuple[Port, ...] = ()

    def ports(self) -> tuple[Port, ...]:
        return self.left + self.right + self.down

    def __post_init__(self) -> None:
        total = len(self.ports())
        if total == 0:
            raise ValueError("empty symbol partition")
        if total > MAX_PINS_PER_BOX:
            raise ValueError(f"partition has {total} pins > {MAX_PINS_PER_BOX}")


def build_symbols(partitions: Iterable[SymbolPartition]) -> list[BoxSymbol]:
    """Turn partitions into one ``BoxSymbol`` each (empty sides skipped)."""
    symbols: list[BoxSymbol] = []
    for part in partitions:
        row = Row(
            left=PinGroup(*part.left) if part.left else (),
            right=PinGroup(*part.right) if part.right else (),
        )
        columns = Column(down=PinGroup(*part.down)) if part.down else ()
        symbols.append(BoxSymbol(rows=row, columns=columns))
    return symbols


def build_pad_mapping(
    lp: VersalBGA,
    assignments: Iterable[tuple[Port, tuple[int, int]]],
    expected_total: int,
) -> PadMapping:
    """Map every port to its BGA pad, reconciling the ball count.

    ``assignments`` carries zero-indexed ``(row, col)`` grid coordinates as
    emitted by the pinout generator; ``VersalBGA.get_pad`` takes the
    1-indexed ball column, so the ``+ 1`` lives here and nowhere else.
    """
    mapping: dict[Port, list[Pad]] = {}
    seen: set[tuple[int, int]] = set()
    for port, (row, col) in assignments:
        if (row, col) in seen:
            raise ValueError(f"duplicate ball assignment at {(row, col)}")
        seen.add((row, col))
        if port in mapping:
            raise ValueError(f"port assigned twice: {port} at {(row, col)}")
        mapping[port] = [lp.get_pad(row, col)]
    if len(mapping) != expected_total:
        raise ValueError(
            f"ball count mismatch: {len(mapping)} assignments, "
            f"expected {expected_total}"
        )
    return PadMapping(mapping)
