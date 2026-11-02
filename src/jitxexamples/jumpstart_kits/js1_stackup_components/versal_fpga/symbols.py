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

Partitioning rules
    At 1369 balls there is no single readable symbol: the partition is the
    part's schematic, so it is stated as rules and held by checks. The
    policy lives in ``tools.generate_pinout.partition_symbols``.

    * One box per structural group the source document defines. The AMD
      package pinout file (``xcvp1002nfvi1369pkg.txt``) has a ``Bank``
      column, so every banked ball (I/O pins, the transceiver quad pins of
      the GTM and GTY banks, and the bank's own supplies) goes to its
      bank's box. On another part, take the grouping from the axis its pin table
      is organized by (I/O bank, transceiver quad, power domain, peripheral
      block). A grouping whose defining document cannot be named is
      invented.
    * A stated per-box ceiling for groups with no natural size. The
      bankless rails would otherwise be single boxes of hundreds of pins
      (689 ``GND`` balls, 84 ``VCCINT``); they are chunked at
      ``MAX_PINS_PER_BOX``, and the smaller bankless rails are packed
      together up to the same ceiling. ``SymbolPartition`` rejects a box
      over the cap at instantiation, and the test suite checks every box
      against it and checks that the generator's copy of the constant
      matches. Pick the number by looking at the rendered sheet at the
      schematic's page size, then keep the test that enforces it.
    * Every port in exactly one partition, asserted by a test
      (``test_symbol_coverage`` in ``tests/test_js1_versal_fpga.py``): no
      port seen twice, whether across boxes or inside one, and the union of
      all boxes equals every port of the component. The duplicate inside
      one box needs the test because nothing else reports it: ``BoxSymbol``
      maps each port to one pin, so a port listed twice in a box keeps only
      its last pin and leaves the first unmapped.
    * Pins that belong to no group get their own box. Bankless dedicated
      and analog pins share one "Dedicated / analog singletons" box rather
      than being spread across other boxes for convenience.
    * Regular fixed-size slices only for parts with no functional
      structure: generic connectors, board-to-board headers, pin arrays. An
      FPGA, MCU or memory is partitioned by the structure its datasheet
      gives first.

Schematic groups
    :class:`.circuit.XCVP1002Circuit` puts each box in its own
    ``SchematicGroup`` (one per ``Symbol`` from ``extract(self.fpga,
    Symbol)``) so banks and rail chunks can be placed on separate sheets.
    A rail spread over several boxes stays one named net, and named nets
    are labeled in the schematic, so the boxes connect through net labels
    rather than drawn wires.
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
