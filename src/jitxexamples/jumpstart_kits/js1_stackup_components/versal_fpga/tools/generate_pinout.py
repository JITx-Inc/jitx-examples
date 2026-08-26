"""Generate the XCVP1002 component module from an AMD package pinout file.

Usage (from the repository root, any Python 3.12+, stdlib only)::

    python -m jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.\\
tools.generate_pinout <pinout.txt> [--out FILE] [--report] [--check]

Input
    The AMD ASCII package pinout file for the VP1002 in NFVI1369
    (``xcvp1002nfvi1369pkg.txt``), downloaded by the user from AMD's "Versal
    Adaptive SoC Package Device Pinout Files" page. The file is proprietary
    to AMD and is **never committed** — keep it in the git-ignored
    ``.context/`` directory. Only the factual pin name/position data it
    describes is embedded in the generated Python module, with provenance.

Output
    ``xcvp1002.py`` next to this package's other modules: a declarative
    ``jitx.Component`` with one ``Port`` per ball (indexed lists for repeated
    rail names), zero-indexed ball coordinates, GTM quad groupings, and
    symbol partitions. Deterministic: same input file -> byte-identical
    output (``--check`` re-generates and diffs against the committed file).

Doctrine
    No string-keyed runtime models and no ``getattr`` in the emitted code:
    every pin reference in the generated module is an explicit attribute
    expression. Ball references ("AB34") exist only here, at generation
    time, where they are converted to ``(row, col)`` grid coordinates.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

#: BGA row letters in order; I, O, Q, S, X, Z are skipped (JEDEC/AMD style).
ROW_LOOKUP = "ABCDEFGHJKLMNPRTUVWY"

AMD_PINOUT_FILES_URL = (
    "https://www.amd.com/en/developer/resources/adaptive-socs-and-fpgas/"
    "package-pinout-files/versal-package-device-pinout-files.html"
)
AM013_URL = "https://docs.amd.com/r/en-US/am013-versal-pkg-pinout"

TOOL_MODULE = (
    "jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga."
    "tools.generate_pinout"
)

NFVI_CODE = "NFVI1369"

#: Pins per box when chunking large rails into symbol boxes. Restates
#: ``symbols.MAX_PINS_PER_BOX`` because this tool is deliberately
#: stdlib-only (it must run without a jitx environment); the owner enforces
#: the cap at instantiation (``SymbolPartition.__post_init__``) and the test
#: suite asserts the two values stay equal.
MAX_PINS_PER_BOX = 64

GTM_LANE_RE = re.compile(r"^GTM_(RX|TX)([PN])(\d)_(\d{3})$")
GTM_REFCLK_RE = re.compile(r"^GTM_REFCLK([PN])(\d)_(\d{3})$")


@dataclass(frozen=True)
class PinEntry:
    """One data row of the pinout file."""

    ball: str
    name: str
    bank: str
    io_type: str
    slr: str
    perf: str
    ddrmc: str
    row: int
    col: int


@dataclass(frozen=True)
class Pinout:
    """Parsed pinout file plus its own provenance lines."""

    source_name: str
    sha256: str
    provenance: tuple[str, ...]
    entries: tuple[PinEntry, ...]
    total_from_footer: int
    num_rows: int
    num_cols: int


def ball_to_rc(ball: str) -> tuple[int, int]:
    """``"AB34" -> (21, 33)`` — zero-indexed (row, col) grid coordinates."""
    m = re.fullmatch(r"([A-Z]+)(\d+)", ball)
    if m is None:
        raise ValueError(f"malformed ball reference: {ball!r}")
    letters, digits = m.groups()
    row = -1
    for ch in letters:
        idx = ROW_LOOKUP.find(ch)
        if idx < 0:
            raise ValueError(f"invalid row letter {ch!r} in {ball!r}")
        row = (row + 1) * len(ROW_LOOKUP) + idx
    col = int(digits)
    if col < 1:
        raise ValueError(f"column must be >= 1 in {ball!r}")
    return row, col - 1


def rc_to_ball(row: int, col: int) -> str:
    """Inverse of :func:`ball_to_rc`, for round-trip self-checks."""
    if row < 0 or col < 0:
        raise ValueError(f"negative grid coordinate: {(row, col)}")
    letters = ""
    r = row
    while r >= 0:
        letters = ROW_LOOKUP[r % len(ROW_LOOKUP)] + letters
        r = r // len(ROW_LOOKUP) - 1
    return f"{letters}{col + 1}"


def parse_pinout(text: str, source_name: str) -> Pinout:
    """Parse the AMD ASCII pinout file; fail loudly on any surprise."""
    provenance: list[str] = []
    entries: list[PinEntry] = []
    total_from_footer: int | None = None
    header_seen = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("--"):
            body = line.lstrip("-").strip()
            if re.match(r"(Device|Package|Family|Date|Version)\b", body):
                provenance.append(body)
            continue
        tokens = line.split()
        if tokens[0] == "Pin":
            header_seen = True
            continue
        if line.startswith("Total Number of Pins"):
            total_from_footer = int(tokens[-1])
            continue
        if not header_seen:
            continue
        if len(tokens) != 7:
            raise ValueError(f"expected 7 columns, got {len(tokens)}: {line!r}")
        ball, name, bank, io_type, slr, perf, ddrmc = tokens
        row, col = ball_to_rc(ball)
        if rc_to_ball(row, col) != ball:
            raise ValueError(f"ball reference round-trip failed for {ball!r}")
        entries.append(PinEntry(ball, name, bank, io_type, slr, perf, ddrmc, row, col))
    if total_from_footer is None:
        raise ValueError("missing 'Total Number of Pins' footer")
    if len(entries) != total_from_footer:
        raise ValueError(
            f"row count {len(entries)} != footer total {total_from_footer}"
        )
    balls = [e.ball for e in entries]
    if len(set(balls)) != len(balls):
        dupes = [b for b, n in Counter(balls).items() if n > 1]
        raise ValueError(f"duplicate ball references: {dupes}")
    num_rows = max(e.row for e in entries) + 1
    num_cols = max(e.col for e in entries) + 1
    if num_rows * num_cols != len(entries):
        raise ValueError(
            f"grid {num_rows}x{num_cols} is not fully populated "
            f"({len(entries)} balls) — depopulated packages need a grid "
            "planner; this generator only supports full grids"
        )
    # Hash the newline-normalized text (as read), not the raw bytes: the AMD
    # file ships CRLF, so `shasum` on the download will differ. The --check
    # mode and the idempotency test both hash the same way, so the recorded
    # value stays comparable.
    sha = hashlib.sha256(text.encode()).hexdigest()
    return Pinout(
        source_name=source_name,
        sha256=sha,
        provenance=tuple(provenance),
        entries=tuple(entries),
        total_from_footer=total_from_footer,
        num_rows=num_rows,
        num_cols=num_cols,
    )


def natural_key(name: str) -> tuple:
    """Sort key treating digit runs numerically (L2 before L10)."""
    return tuple(
        int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)
    )


@dataclass(frozen=True)
class PinModel:
    """Classified pinout: repeated rail names vs unique pin names."""

    pinout: Pinout
    rails: dict[str, tuple[PinEntry, ...]]  # name -> entries, (row, col) order
    uniques: dict[str, PinEntry]  # name -> entry


def classify(pinout: Pinout) -> PinModel:
    counts = Counter(e.name for e in pinout.entries)
    rails: dict[str, list[PinEntry]] = {}
    uniques: dict[str, PinEntry] = {}
    for e in pinout.entries:
        if counts[e.name] > 1:
            rails.setdefault(e.name, []).append(e)
        else:
            uniques[e.name] = e
    for name in rails:
        rails[name].sort(key=lambda e: (e.row, e.col))
    bad = [n for n in counts if not n.isidentifier()]
    if bad:
        raise ValueError(f"pin names are not Python identifiers: {bad}")
    return PinModel(
        pinout=pinout,
        rails={n: tuple(v) for n, v in sorted(rails.items())},
        uniques=dict(sorted(uniques.items(), key=lambda kv: natural_key(kv[0]))),
    )


@dataclass(frozen=True)
class GTMQuadGroup:
    """Lane/refclk pin names of one GTM bank, index-ordered."""

    bank: int
    rxp: tuple[str, ...]
    rxn: tuple[str, ...]
    txp: tuple[str, ...]
    txn: tuple[str, ...]
    refclkp: tuple[str, ...]
    refclkn: tuple[str, ...]


def gtm_quads(model: PinModel) -> tuple[GTMQuadGroup, ...]:
    """Extract GTM quads from the unique-pin roster; validate completeness."""
    lanes: dict[int, dict[str, dict[int, str]]] = {}
    refclks: dict[int, dict[str, dict[int, str]]] = {}
    for name in model.uniques:
        m = GTM_LANE_RE.fullmatch(name)
        if m:
            direction, polarity, lane, bank = m.groups()
            key = f"{direction.lower()}{polarity.lower()}"
            lanes.setdefault(int(bank), {}).setdefault(key, {})[int(lane)] = name
            continue
        m = GTM_REFCLK_RE.fullmatch(name)
        if m:
            polarity, idx, bank = m.groups()
            key = f"refclk{polarity.lower()}"
            refclks.setdefault(int(bank), {}).setdefault(key, {})[int(idx)] = name
    quads: list[GTMQuadGroup] = []
    for bank in sorted(lanes):
        lane_sets = lanes[bank]
        clk_sets = refclks.get(bank, {})
        parts: dict[str, tuple[str, ...]] = {}
        for key, expected in (
            ("rxp", 4),
            ("rxn", 4),
            ("txp", 4),
            ("txn", 4),
            ("refclkp", 2),
            ("refclkn", 2),
        ):
            source = clk_sets if key.startswith("refclk") else lane_sets
            found = source.get(key, {})
            if sorted(found) != list(range(expected)):
                raise ValueError(
                    f"GTM bank {bank}: {key} indices {sorted(found)} != "
                    f"0..{expected - 1}"
                )
            parts[key] = tuple(found[i] for i in range(expected))
        quads.append(GTMQuadGroup(bank=bank, **parts))
    return tuple(quads)


@dataclass(frozen=True)
class Partition:
    """One symbol box, expressed as emission strings."""

    comment: str
    left: tuple[str, ...]  # python expressions
    right: tuple[str, ...]
    down: tuple[str, ...] = ()


def _attr(name: str) -> str:
    return f"self.{name}"


def _split_half(exprs: list[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    half = (len(exprs) + 1) // 2
    return tuple(exprs[:half]), tuple(exprs[half:])


def partition_symbols(model: PinModel) -> list[Partition]:
    """Symbol partition policy: banks first, then rails packed into boxes."""
    parts: list[Partition] = []
    by_bank: dict[str, list[PinEntry]] = {}
    for e in model.pinout.entries:
        if e.bank != "NA":
            by_bank.setdefault(e.bank, []).append(e)

    def bank_sort_key(bank: str) -> tuple:
        return (len(bank), bank)

    for bank in sorted(by_bank, key=bank_sort_key):
        entries = by_bank[bank]
        rail_names = sorted(
            {e.name for e in entries if e.name in model.rails},
            key=natural_key,
        )
        unique_names = sorted(
            (e.name for e in entries if e.name in model.uniques),
            key=natural_key,
        )
        io_types = {e.io_type for e in entries} - {"NA"}
        label = "/".join(sorted(io_types)) if io_types else "power"
        if any(t in ("GTM", "GTY") for t in io_types):
            rx = [n for n in unique_names if re.search(r"_RX[PN]\d", n)]
            tx = [n for n in unique_names if re.search(r"_TX[PN]\d", n)]
            clk = [n for n in unique_names if "REFCLK" in n]
            other = [n for n in unique_names if n not in {*rx, *tx, *clk}]
            left = tuple(_attr(n) for n in rx)
            right = tuple(_attr(n) for n in tx + clk)
            down = tuple(_attr(n) for n in other) + tuple(
                f"*self.{n}" for n in rail_names
            )
        else:
            left, right = _split_half([_attr(n) for n in unique_names])
            down = tuple(f"*self.{n}" for n in rail_names)
        parts.append(
            Partition(
                comment=f"Bank {bank} ({label})",
                left=left,
                right=right,
                down=down,
            )
        )

    misc = [
        n
        for n, e in model.uniques.items()
        if e.bank == "NA"
        and not GTM_LANE_RE.fullmatch(n)
        and not GTM_REFCLK_RE.fullmatch(n)
    ]
    if misc:
        left, right = _split_half([_attr(n) for n in sorted(misc, key=natural_key)])
        parts.append(Partition("Dedicated / analog singletons", left, right))

    bankless_rails = [(n, len(v)) for n, v in model.rails.items() if v[0].bank == "NA"]
    bankless_rails.sort(key=lambda item: (-item[1], natural_key(item[0])))
    pending: list[tuple[str, int, int, int]] = []  # (name, start, stop, size)
    pending_total = 0

    def flush() -> None:
        nonlocal pending, pending_total
        if not pending:
            return
        if len(pending) == 1 and pending[0][3] > MAX_PINS_PER_BOX // 2:
            # A lone large rail would otherwise stack one-sided; split it.
            name, a, b, size = pending[0]
            mid = a + (b - a + 1) // 2
            pending = [(name, a, mid, size), (name, mid, b, size)]
        exprs = [
            f"*self.{n}[{a}:{b}]" if (a, b) != (0, size) else f"*self.{n}"
            for n, a, b, size in pending
        ]
        counts = [b - a for _, a, b, _ in pending]
        total = sum(counts)
        acc, split_at = 0, len(exprs)
        for i, c in enumerate(counts):
            if acc + c > total // 2 and i > 0:
                split_at = i
                break
            acc += c
        names = ", ".join(dict.fromkeys(n for n, *_ in pending))
        parts.append(
            Partition(
                comment=f"Power/ground: {names}",
                left=tuple(exprs[:split_at]),
                right=tuple(exprs[split_at:]),
            )
        )
        pending, pending_total = [], 0

    for name, size in bankless_rails:
        if size > MAX_PINS_PER_BOX:
            flush()
            for start in range(0, size, MAX_PINS_PER_BOX):
                stop = min(start + MAX_PINS_PER_BOX, size)
                mid = start + (stop - start + 1) // 2
                parts.append(
                    Partition(
                        comment=f"Power/ground: {name}[{start}:{stop}]",
                        left=(f"*self.{name}[{start}:{mid}]",),
                        right=(f"*self.{name}[{mid}:{stop}]",),
                    )
                )
            continue
        if pending_total + size > MAX_PINS_PER_BOX:
            flush()
        pending.append((name, 0, size, size))
        pending_total += size
    flush()
    return parts


def _fmt_coord_table(name: str, entries: tuple[PinEntry, ...]) -> list[str]:
    lines = [
        "# fmt: off",
        f"_{name}_BALLS: tuple[tuple[int, int], ...] = (",
    ]
    row: list[str] = []
    for e in entries:
        row.append(f"({e.row}, {e.col}),")
        if len(row) == 7:
            lines.append("    " + " ".join(row))
            row = []
    if row:
        lines.append("    " + " ".join(row))
    lines.append(")")
    lines.append("# fmt: on")
    return lines


def _emit_partition(part: Partition) -> list[str]:
    lines = [f"        # {part.comment}"]
    lines.append("        yield SymbolPartition(")
    for side in ("left", "right", "down"):
        exprs = {"left": part.left, "right": part.right, "down": part.down}[side]
        if not exprs:
            continue
        inline = f"            {side}=({exprs[0]},),"
        if len(exprs) == 1 and len(inline) <= 88:
            lines.append(inline)
            continue
        lines.append(f"            {side}=(")
        for expr in exprs:
            lines.append(f"                {expr},")
        lines.append("            ),")
    lines.append("        )")
    return lines


def emit_module(model: PinModel) -> str:
    pinout = model.pinout
    quads = gtm_quads(model)
    parts = partition_symbols(model)

    unique_by_section: dict[str, list[str]] = {}
    for name, e in model.uniques.items():
        section = f"Bank {e.bank}" if e.bank != "NA" else "Dedicated / bankless"
        unique_by_section.setdefault(section, []).append(name)

    def section_key(s: str) -> tuple:
        return (s == "Dedicated / bankless", len(s), s)

    L: list[str] = []
    provenance = "\n".join(f"    {p}" for p in pinout.provenance)
    L.append('"""AMD Versal Premium VP1002, NFVI1369 package — GENERATED MODULE.')
    L.append("")
    L.append(f"Generated by ``python -m {TOOL_MODULE}``. DO NOT EDIT BY HAND —")
    L.append("regenerate from the AMD package pinout file instead.")
    L.append("")
    L.append("Ground truth")
    L.append(f"    * ``{pinout.source_name}`` (AMD package device pinout file,")
    L.append(f"      sha256 ``{pinout.sha256[:16]}...`` of the newline-")
    L.append("      normalized text), downloaded from")
    L.append(f"      {AMD_PINOUT_FILES_URL}")
    if provenance:
        L.append("      File header identification lines:")
        L.append(provenance)
    L.append('    * AM013 "Package Dimensions for NFVI1369" (mechanical) and')
    L.append('      "BGA Package Design Rules" (PCB land rules), via')
    L.append("      ``.landpattern`` -- cited by caption because AM013")
    L.append("      renumbers its figures between editions; see")
    L.append("      ``landpattern.AM013_MECHANICAL_FIGURE`` for the edition")
    L.append("      and page each value was read from:")
    L.append(f"      {AM013_URL}")
    L.append("")
    L.append("Structure")
    L.append(
        f"    {pinout.total_from_footer} balls on a full "
        f"{pinout.num_rows}x{pinout.num_cols} grid, 0.92 mm pitch."
    )
    L.append("    Every ball has exactly one ``Port``: unique pin names are")
    L.append("    scalar attributes; repeated rail names (GND, VCCINT, VCCO_*,")
    L.append("    NC, ...) are indexed lists ordered by (row, col). Ball")
    L.append("    coordinates are zero-indexed grid positions; the ball")
    L.append('    reference strings ("A1") exist only in the generator.')
    L.append("")
    L.append("The ordering-code suffix (speed/temperature grade) is omitted from")
    L.append("``mpn``; see DS959 for full ordering information.")
    L.append('"""')
    L.append("")
    L.append("from collections.abc import Iterator")
    L.append("")
    L.append("import jitx")
    L.append("from jitx.net import Port")
    L.append("")
    L.append("from .bundles import GTMQuadPins")
    L.append("from .landpattern import NFVI1369, make_landpattern")
    L.append("from .symbols import SymbolPartition, build_pad_mapping, build_symbols")
    L.append("")
    L.append(f'PINOUT_SHA256 = "{pinout.sha256}"')
    L.append(f"TOTAL_BALLS = {pinout.total_from_footer}")
    L.append("")
    L.append("")
    L.append("class XCVP1002(jitx.Component):")
    L.append('    """AMD Versal Premium VP1002 FPGA in the NFVI1369 package."""')
    L.append("")
    L.append(f'    mpn = "XCVP1002-{NFVI_CODE}"')
    L.append('    manufacturer = "AMD"')
    L.append(f'    datasheet = "{AM013_URL}"')
    L.append('    reference_designator_prefix = "U"')
    for section in sorted(unique_by_section, key=section_key):
        L.append("")
        L.append(f"    # --- {section} ---")
        for name in unique_by_section[section]:
            L.append(f"    {name} = Port()")
    L.append("")
    L.append("    # --- Repeated rails (indexed lists, (row, col) order) ---")
    for name, entries in model.rails.items():
        L.append(f"    {name} = [Port() for _ in range({len(entries)})]")
    L.append("")
    L.append("    landpattern = make_landpattern(NFVI1369)")
    L.append("")
    L.append(
        "    def ball_assignments(self) -> Iterator[tuple[Port, tuple[int, int]]]:"
    )
    L.append('        """Yield every (port, zero-indexed grid coordinate) pair."""')
    for section in sorted(unique_by_section, key=section_key):
        L.append(f"        # {section}")
        for name in unique_by_section[section]:
            e = model.uniques[name]
            L.append(f"        yield self.{name}, ({e.row}, {e.col})  # {e.ball}")
    for name in model.rails:
        L.append(f"        yield from zip(self.{name}, _{name}_BALLS, strict=True)")
    L.append("")
    L.append("    def gtm_quad_pins(self) -> dict[int, GTMQuadPins]:")
    L.append('        """Structural lane/refclk pins of each GTM bank."""')
    L.append("        return {")
    for quad in quads:
        L.append(f"            {quad.bank}: GTMQuadPins(")
        for field in ("rxp", "rxn", "txp", "txn", "refclkp", "refclkn"):
            names = {
                "rxp": quad.rxp,
                "rxn": quad.rxn,
                "txp": quad.txp,
                "txn": quad.txn,
                "refclkp": quad.refclkp,
                "refclkn": quad.refclkn,
            }[field]
            L.append(f"                {field}=(")
            for n in names:
                L.append(f"                    self.{n},")
            L.append("                ),")
        L.append("            ),")
    L.append("        }")
    L.append("")
    L.append("    def symbol_partitions(self) -> Iterator[SymbolPartition]:")
    L.append('        """Yield the schematic box partitions (see .symbols)."""')
    for part in parts:
        L.extend(_emit_partition(part))
    L.append("")
    L.append("    def __init__(self):")
    L.append("        self.mappings = [")
    L.append(
        "            build_pad_mapping(self.landpattern, "
        "self.ball_assignments(), TOTAL_BALLS)"
    )
    L.append("        ]")
    L.append("        self.symbols = build_symbols(self.symbol_partitions())")
    L.append("")
    L.append("")
    L.append("# Ball coordinate tables for the rail lists, (row, col) sorted.")
    for name, entries in model.rails.items():
        L.extend(_fmt_coord_table(name, entries))
    L.append("")
    L.append("Device: type[XCVP1002] = XCVP1002")
    L.append("")
    return "\n".join(L)


def inventory_report(model: PinModel) -> str:
    pinout = model.pinout
    lines = [
        f"source: {pinout.source_name}  sha256: {pinout.sha256[:16]}...",
        f"grid: {pinout.num_rows}x{pinout.num_cols} full  "
        f"balls: {len(pinout.entries)} (footer {pinout.total_from_footer})",
        "",
        f"{'group':38} {'kind':8} {'balls':>5}",
    ]
    total = 0
    for name, entries in model.rails.items():
        bank = entries[0].bank
        kind = "rail" if bank == "NA" else f"rail/{bank}"
        lines.append(f"{name:38} {kind:8} {len(entries):>5}")
        total += len(entries)
    by_bank = Counter(
        e.bank if e.bank != "NA" else "(bankless uniques)"
        for e in model.uniques.values()
    )
    for bank, count in sorted(by_bank.items(), key=lambda kv: (len(kv[0]), kv[0])):
        lines.append(f"{'unique pins, bank ' + bank:38} {'unique':8} {count:>5}")
        total += count
    lines.append(f"{'TOTAL':38} {'':8} {total:>5}")
    lines.append("")
    quads = gtm_quads(model)
    lines.append(f"GTM quads: {[q.bank for q in quads]}")
    if total != pinout.total_from_footer:
        lines.append(f"RECONCILIATION FAILED: {total} != {pinout.total_from_footer}")
    else:
        lines.append(f"reconciled: {total} == {pinout.total_from_footer}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pinout_file", type=Path)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "xcvp1002.py",
    )
    parser.add_argument("--report", action="store_true", help="print inventory")
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate and diff against --out; exit 1 on drift",
    )
    args = parser.parse_args(argv)
    text = args.pinout_file.read_text()
    model = classify(parse_pinout(text, args.pinout_file.name))
    if args.report:
        print(inventory_report(model))
        return 0
    emitted = emit_module(model)
    if args.check:
        committed = args.out.read_text()
        if committed == emitted:
            print(f"OK: {args.out} matches regeneration")
            return 0
        diff = difflib.unified_diff(
            committed.splitlines(), emitted.splitlines(), "committed", "regenerated"
        )
        sys.stdout.writelines(line + "\n" for line in list(diff)[:60])
        return 1
    args.out.write_text(emitted)
    counts = f"{len(model.uniques)} unique ports, {len(model.rails)} rails"
    print(f"wrote {args.out} ({counts}, {model.pinout.total_from_footer} balls)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
