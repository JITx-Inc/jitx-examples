# jitx-examples

## What this is

`jitxexamples` is a library of example JITX package contents:

- **Components**: Python classes that model real, sourceable electronic parts (op-amps, FETs, MCUs, regulators, connectors, sensors, etc.) for use with the JITX PCB design framework.
- **Substrates**: reusable PCB stackups, via definitions, and fabrication constraints.
- **Designs**: buildable example boards that compose package components, substrates, routing rules, and geometry into complete JITX designs.

## Commands

```bash
hatch test --cover        # run the test suite with coverage (canonical, per README)
hatch fmt --check         # check formatting/lint (ruff 0.14.9, config in pyproject)
hatch run types:check     # pyright type check
hatch run types:stats     # pyright stats

pytest tests/test_AO3401A.py            # run a single test file
pytest tests/test_AO3401A.py -k ao3401a # run a single test
```

### Run designs

JITX design builds require an installed and running JITX runtime. From the project root:

```bash
jitx runtime start --background
jitx find
jitx build jitxexamples.designs.si_bga_optimization.bga_escape.bga_optimization_design
jitx ui open --board --design jitxexamples.designs.si_bga_optimization.bga_escape.bga_optimization_design
```

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

### Substrate definitions (`src/jitxexamples/substrates/`)
Substrates define reusable PCB construction details. `generic_20layer.py` provides `Generic_Substrate`, a generic 20-layer stackup with dielectric/conductor materials, fabrication constraints, and via classes that designs can use directly or specialize.

### Design definitions (`src/jitxexamples/designs/`)
Designs are buildable JITX `SampleDesign` classes. The SI BGA optimization example lives under `designs/si_bga_optimization/`; its build target is `jitxexamples.designs.si_bga_optimization.bga_escape.bga_optimization_design`.

Within that design package, `constraints.py` defines the design-rule `Tag` subclasses and the antipad fence-via `design_constraint` rules; `substrate.py` specializes the generic substrate with the 85 ohm stripline routing structure and per-signal-layer launch profiles (`BGAEscapeSubstrate`), anchoring the fence rules into the design tree; `si_geometry.py` builds the per-lane signal-via antipad, deskew-arc, GND-stitching, and board-level SI-cutout geometry, including the HFSS-instrumented-lane override; and `bga_escape.py` assembles the per-lane `EscapeLane` circuits into the top-level `BGALink` and holds the buildable `bga_optimization_design` entry point. `generic_bga.py` defines the reusable hex-grid BGA component used by the design, and `deskew.py` contains support geometry for the BGA diff-pair deskew copper.

### Tests (`tests/`)
One `test_*.py` per component. Tests subclass `jitx.test.TestCase` (a `unittest.TestCase` that activates the JITX *instantiation context* in `setUpClass` — required so that JITX class members instantiate correctly; do not use plain `unittest.TestCase` for code that builds design elements). A test typically defines a `SampleDesign` subclass containing an `@inline class circuit(Circuit)` that instantiates the component, then asserts on the built design.

## Dependencies & environment

Requires Python ≥3.12; the test matrix covers 3.12/3.13/3.14. Built with hatchling + hatch-vcs (version derived from git tags). Core deps: `jitx` (4.x), `jitxlib-standard`, `jitxlib-parts`, `jitxlib-voltage-divider`, `eseries`. The wheel packages `src/jitxexamples`; `docs/` is excluded from both pyright and `[tool.jitx]`.
