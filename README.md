# jitx-examples

## What this is

`jitxexamples` is a library of example JITX package contents:

- **Components**: Python classes that model real, sourceable electronic parts (op-amps, FETs, MCUs, regulators, connectors, sensors, etc.) for use with the JITX PCB design framework.
- **Substrates**: reusable PCB stackups, via definitions, and fabrication constraints.
- **Patterns**: small single-technique modules, each with a design that translates.
- **Demos**: buildable example boards that compose package components, substrates, routing rules, and geometry into complete JITX designs.

## Commands

```bash
hatch test --cover        # run the test suite with coverage (canonical, per README)
hatch fmt --check         # check formatting/lint (ruff 0.14.9, config in pyproject)
hatch run types:check     # pyright type check
hatch run types:stats     # pyright stats

pytest tests/test_AO3401A.py            # run a single test file
pytest tests/test_AO3401A.py -k ao3401a # run a single test
```

### Run demos

JITX design builds require an installed and running JITX runtime. From the project root:

```bash
jitx runtime start --background
jitx design find
jitx design build jitxexamples.demos.si_bga_optimization.bga_escape.bga_optimization_design
jitx ui open --board --design jitxexamples.demos.si_bga_optimization.bga_escape.bga_optimization_design
```

Build the explicit non-test design target above; do not substitute similarly named targets from
`test`, `tests`, or a test file listed by `jitx design find`.

`jitx design build` writes its output to `<repo-root>/designs/<module.path.design_name>/`
(`design-info/`, `temp/`, ...). That directory name is chosen by JITX, not by this repo, and is
git-ignored — which is why the Python sources live in `src/jitxexamples/demos/` rather than
`src/jitxexamples/designs/`.

The git `pre-commit` hook (`hooks/pre-commit`) runs `ruff check`, `ruff format --diff`, and `python -m unittest discover` on staged Python files. Install it with `git config core.hooksPath hooks` (or symlink into `.git/hooks/`).

Lint is intentionally narrow: ruff `select = ["E","F","W","A","B","C"]` with `E501`, `A005`, `C901`, `A002` ignored. Line length 88, double quotes.

## Architecture

### Component definitions (`src/jitxexamples/components/<category>/`)
Components are grouped into category packages (`opamps/`, `fets_n_ch/`, `mcus/`, `connectors/`, ...). Each `.py` file defines one component as a subclass of `jitx.Component`. The `__init__.py` files are empty — components are imported by their full module path (e.g. `from jitxexamples.components.fets_p_ch.AO3401A import AO3401A`).

A component class is declarative. The standard shape (see `components/opamps/texas_instruments_OPA189.py`):
- Metadata class attributes: `mpn`, `manufacturer`, `reference_designator_prefix`, `datasheet`.
- `Port()` attributes for each pin/signal.
- A `landpattern` built from a footprint generator (`jitxlib.landpatterns.generators.*`, e.g. `SOT23_5`) configured with `LeadProfile` and `jitx.Toleranced` dimensions.
- A `symbol` from `jitxlib.symbols.*`.
- A `mappings` list of `jitx.PadMapping` (port → `landpattern.p[n]`) and `jitx.SymbolMapping` (port → symbol pin).

Some files ship an accompanying `.stp` (3D STEP model) alongside the `.py`. Some components also alias the class as `Device: type[...] = ...`.

### JumpStart kit reference solutions (`src/jitxexamples/jumpstart_kits/`)
Importable reference solutions for the JumpStart kit runbooks published from `jumpstart-kits/`
(one package per kit, e.g. `js1_stackup_components/`, with one subpackage per task deliverable:
`hdi_stackup/`, `versal_fpga/`). These are covered by the same ruff, pyright, and pytest gates as
the rest of the package. The learner-facing runbooks and supplied inputs live in `jumpstart-kits/`
at the repo root (published to the docs site), not here.

### Substrate definitions (`src/jitxexamples/substrates/`)
Substrates define reusable PCB construction details. `generic_20layer.py` provides `Generic_Substrate`, a generic 20-layer stackup with dielectric/conductor materials, fabrication constraints, and via classes that designs can use directly or specialize.

### Pattern definitions (`src/jitxexamples/patterns/`)
Patterns are small modules that each show one technique, written to be read; each ends in a design that translates with `jitx design build --dry`. `fenced_pour_outline.py` fences an arbitrary closed outline (an antipad, an RF cavity, a BGA breakout) with vias: a `Tag`, a `design_constraint(...).fence_via(...)` rule on the substrate, and a tagged `Pour` inside a `FencedOutline` circuit whose `GND` port connects to the board's ground net. A `KeepOut` over the same outline, which keeps pours and auto-placed vias out of the opening, is optional; the module adds one. Its design target is `jitxexamples.patterns.fenced_pour_outline.fenced_pour_outline_design`. To see the fence, run a full build (`jitx design build <target>`, which needs the runtime) and open the board with `jitx ui open --board --design <target>`. The module also has `CavityRing`, a closed ring turned inwards (a negative `offset`) so its vias land in a ground cavity pour's own copper, with a same-net anchor via; its target is `jitxexamples.patterns.fenced_pour_outline.cavity_ring_design`. `fence_count_range` gives the via counts to accept along an outline before a build is checked.

The `layout_*` modules each show one design-rule technique on jitx 4.6. Each has offline tests and a runtime test, gated by `JITX_PATTERN_RUNTIME=1`, that measures the computed copper. Pours and vias: `layout_default_rules` (board defaults for trace width, clearance and pad relief, checked against the fab floors, with rules on power and ground net tags at a higher priority), `layout_thermal_classes` (relief per pad class chosen from the measured pad size, plus a direct connect on an exposed pad and an untagged part that joins its pour solidly because no relief rule matches it), `layout_heavy_copper_layer` (floors for one heavy inner layer with `OnLayer` on the priority ladder, with `heavy_layer_index` to find the layer and `heavy_layer_rules` to write the floors and the copies of the net-tag rules), `layout_stitched_pour` (a `stitch_via` rule on a pour tag, its pitch checked against the via and the fab, and `expected_stitch_sites` for the sites a build must fill) and `layout_edge_and_cutout` (pour pullback from the board edge with `IsBoardEdge`, and from cutouts, outline holes and via drills with `IsHole`). Routing: `layout_cpwg_two_row_fence` (a grounded coplanar line with two rows of fence vias, fenced through its routing structure, with functions for the coplanar gap, the row positions and counts, and the rows that reach the pour), `layout_qfn_escape` (a power trace stepped down to fit a QFN pad, with `escape_width` deriving the width from the pad, the nearest other pad and a chosen escape clearance), `layout_bga_escape` (a power trace stepped down to pass between BGA balls, with the width read from the balls), `layout_diff_pair_escape` (two differential pairs necked down at a fine-pitch device and held apart in the run, by tags on the routes), `layout_sensitive_net_clearance` (a clearance between the tags on an RF net and a switch-node net: the switch-node pour pulls back from the RF line while a GND pour stays at its default clearance) and `layout_routing_structure_by_tag` (routing structures applied by tag, with a neck structure on the escape).

The `si_*` modules each show one signal-integrity constraint on jitx 4.6, on plain nets with code routes that close the path, and their docstrings paste the design-issues output they produced: `si_point_to_point` (timing and loss with a `TerminatingPinModel`), `si_series_part` (a `BridgingPinModel` through a series part), `si_via_model` (a via with `models`), `si_diff_pair` (intra-pair skew), `si_bundle_skew` (skew across pairs with `ConstrainReferenceDifference`), `si_daisy_chain` (an ordered chain with `>>`), `si_via_structure` (a via structure from `jitxlib.via_structures`) and `si_signal_constraint` (a `SignalConstraint` subclass); `si_parts` holds their fictional parts. The `pin_*` modules show SI constraints on pin-assigned paths: `pin_lane_polarity` (lane choice and P/N inversion on a provider that is one end of the path) and `pin_series_array` (channel choice through a pass-through part, both sides in one mapping). The `jitx-interconnect-constraints` and `jitx-pin-assignment` skills point at them as worked patterns.

The code-layout modules each build a piece of physical layout in code: `code_route_basics` (code routes on one layer: a plain route, a `Route.Sketch` detour past a via column, and `Route.Config` overrides for trace width, trace space and a destination target, one of which tapers the trace into its pad), `serpentine_sections` (length-matched sections on four differential pairs, each a chain of code routes through `PairInsertion` and `PairPoint` control points whose section between the two `PairPoint`s may meander, each pair under its own serpentine or deskew rule), `wilkinson_tree` (a fenced 1:4 Wilkinson divider tree built from one 1:2 cell, with code routes from an input connector to four outputs and a timing constraint that matches the four paths; each line leaves its pad straight to a `RoutePoint`, and each that turns bends around a tagged ground copper square, and each divider body is fenced like a trace by a fence pour equal to its copper), `rf_connector_launch` (an SMA end launch into a fenced grounded coplanar line: a straight exit to a `RoutePoint` on the pad's axis, a small tagged ground copper square past it whose clearance rule to the line sets the bend radius, and a hyperbolic cutout in the ground under the centre pad), `hex_bga_escape` (two differential pairs out of a hex-grid BGA, split at a `PairPoint` at the ball field's edge so a tagged neck structure runs through the field and the full structure outside it), `qfn_thermal_and_power_fanout` (a grid of thermal vias in the RP2040's exposed pad with a matching soldermask and paste opening, and its `IOVDD` pins fanned out through escapes, trunks and vias to a 3.3 V plane) and `board_ground_pours` (a `GND` pour on every copper layer, all held by one through `GND` anchor via and pulled back from the board edge by an `IsBoardEdge` rule). Each has offline tests and a runtime test, gated by `JITX_PATTERN_RUNTIME=1`, that builds the design and measures the realized copper; run the runtime tests with a JITX runtime started at the repository root.

### Protocol definitions (`src/jitxexamples/protocols/`)
High-speed protocols that `jitxlib.protocols` does not ship: port bundles plus a `SignalConstraint` whose skew limits cite their source and its scope in the module docstring. Each protocol module has a worked example beside it named `<protocol>_example.py`, a `SampleDesign` that nets a fictional controller to a real memory part and applies the constraint without `>>`. Today that is `memory/lpddr4.py` (Micron MT53E1G32D2FW-046 WT:B, an LPDDR4X/LPDDR4 part, target `jitxexamples.protocols.memory.lpddr4_example.LPDDR4ExampleDesign`) and `memory/ddr4.py` (Micron MT40A1G16TB-062E:F, target `jitxexamples.protocols.memory.ddr4_example.DDR4ExampleDesign`). The examples are not routed, so the design issues (each example's docstring shows the `issues(satisfied=True)` call) list each constrained path as `Unconnected Topology` until the board is routed.

### Demo definitions (`src/jitxexamples/demos/`)
Demos are buildable JITX `SampleDesign` classes. The SI BGA optimization example lives under `demos/si_bga_optimization/`; its build target is `jitxexamples.demos.si_bga_optimization.bga_escape.bga_optimization_design`.

Within that demo package, `constraints.py` defines the design-rule `Tag` subclasses and the antipad fence-via `design_constraint` rules; `substrate.py` specializes the generic substrate with the 85 ohm stripline routing structure and per-signal-layer launch profiles (`BGAEscapeSubstrate`), anchoring the fence rules into the design tree; `si_geometry.py` builds the per-lane signal-via antipad, deskew-arc, GND-stitching, and board-level SI-cutout geometry, including the HFSS-instrumented-lane override; and `bga_escape.py` assembles the per-lane `EscapeLane` circuits into the top-level `BGALink` and holds the buildable `bga_optimization_design` entry point. `generic_bga.py` defines the reusable hex-grid BGA component used by the design, and `deskew.py` contains support geometry for the BGA diff-pair deskew copper.

### Tests (`tests/`)
One `test_*.py` per component. Tests subclass `jitx.test.TestCase` (a `unittest.TestCase` that activates the JITX *instantiation context* in `setUpClass` — required so that JITX class members instantiate correctly; do not use plain `unittest.TestCase` for code that builds design elements). A test typically defines a `SampleDesign` subclass containing an `@inline class circuit(Circuit)` that instantiates the component, then asserts on the built design.

## Dependencies & environment

Requires Python ≥3.12; the test matrix covers 3.12/3.13/3.14. Built with hatchling + hatch-vcs (version derived from git tags). Core deps: `jitx>=4.6.0rc2,<4.7`, `jitxlib-standard>=4.6.0rc2,<4.7`, `jitxlib-parts>=2.0.0rc1,<3`, `eseries>=1.2.1,<2`, and `shapely>=2.1,<3`. The wheel packages `src/jitxexamples`; `docs/` and `tests/` are excluded from `[tool.jitx]` discovery, while `docs/` is also excluded from pyright.

## Parts configuration

Some component circuits here create `jitxlib.parts.Resistor`, `Capacitor`, or `Inductor` from
electrical constraints with no MPN named, and each query goes to the providers of a parts chain in
order ([jitxlib-parts docs](https://github.com/JITx-Inc/jitxlib-parts#readme)). Your project owns
that chain: the `jitxexamples` wheel carries the example CSV but no chain, and without a chain
resolution stops with `NoChainConfigured`. This repository's `pyproject.toml` sets:

```toml
[tool.jitx.parts]
chain = ["csv:src/jitxexamples/parts/example-passives.csv", "ideal"]
```

The `csv:` path is relative to this repository's root, so it names the source file in a checkout;
a project that installed `jitxexamples` copies the file out instead (below). That CSV is asked
first. It holds real resistors, capacitors, and inductors as an example. Every resistor row has a
`max_power`, except the 0 ohm jumpers, which the datasheet rates by current: their `max_current` is
that rated current. Every inductor row has a `max_current`: the DC current the part carries within
both its temperature-rise and saturation ratings, the lower of the two where the datasheet gives
both. On a resistor row, `rated_voltage_dc` is the datasheet's maximum working (limiting element)
voltage. The voltage across a resistor at its rated power, sqrt(P x R), is lower than that for low
values, so state a resistor's dissipation with `max_power`. The example CSV is not a qualified
approved-vendor list. Columns other than `category`, `mpn`, `manufacturer`, and `datasheet` are
attributes a query can filter or rank on. A bare number gets a unit only in `resistance`,
`capacitance`, `inductance`, `rated_voltage_dc`, `max_current`, `max_power`, and `area`; elsewhere
write the unit (`6.2 GHz`), or a query with units on that column fails with a dimension mismatch.

`ideal` answers only what the CSV could not. Its parts have an MPN starting `IDEAL-`, no
manufacturer, and cannot be ordered. It needs the value pinned to one number and snaps it to E24. It
takes the `case` the query names (the first, if it names several), or 0402 if it names none, and an
exact `tolerance`, or 1% otherwise. It ignores every other filter, including ratings, dielectric,
`mounting`, and `mpn`. So a query the example CSV cannot meet and that names no `case`, such as a 10
µF capacitor rated 56 V or a 10 µH inductor rated 1 A, comes back as an 0402 part with no rating. `ideal`
declines a value range, and a query its snapped value, case, or tolerance does not meet (an exact
4.99 kohm, or a tolerance limit under 1%); such a query must match a CSV row or resolution fails. A
`csv:` path that names no file reads as an empty catalogue with no error, so every query `ideal` can
meet gets an `ideal` part.

`PartsTestDesign` in `tests/parts.py` uses the same chain with locking off, and limits `ideal` to
queries on value, case, and tolerance, so a test fails where a build would drop a filter.

With no `lock` keys set, a build here records the passives it resolves in `parts.lock.json` at the
repository root, `ideal` parts included, and later builds reuse those entries. Adding the real part
to the CSV does not replace an `ideal` part already in the lockfile; delete `parts.lock.json` to
resolve again, and search it or the BOM for `IDEAL-` to see what is left. For a board you intend to
order:

```toml
[tool.jitx.parts]
chain = ["csv:parts/approved-parts.csv"]
lock = "parts.lock.json"
lock-mode = "read-write"
```

A project that installed `jitxexamples` can copy the example in to try these circuits: pass
`importlib.resources.files("jitxexamples") / "parts" / "example-passives.csv"` to `shutil.copy`
with the destination `parts/approved-parts.csv` (the `parts/` directory must exist). The copy is
not an approved list. Every row needs your approval before you order a board built from it.
Point `csv:` at your approved-parts list, starting from the example header: these circuits filter or
rank on `case`, `mounting`, `tolerance`, `type`, `temperature_coefficient_code`, `rated_voltage_dc`,
`max_current`, `self_resonant_frequency`, `quality_factor`, and `material_core`, plus the value
columns. Remove `"ideal"` so that a query your list cannot meet, a column your list lacks, or a
wrong CSV path fails instead of resolving to a part that ignores the filters asked for. Commit the
`parts.lock.json` a build writes, so a catalogue change cannot silently change an existing board;
the `lock` lines spell out the defaults, with paths relative to the project root. To share a
catalogue as package data, use `jitxlib.parts.providers.CsvParts.from_package(...)` or publish a
chain through the `jitxlib-parts-policy` entry point.
