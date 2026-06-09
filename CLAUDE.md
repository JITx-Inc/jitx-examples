# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`jitxexamples` is a library of example JITX **component** definitions — Python classes that model real, sourceable electronic parts (op-amps, FETs, MCUs, regulators, connectors, sensors, etc.) for use with the JITX PCB design framework. It is a parts library, **not** a board design: there is no top-level `main`/design module and no `jitx build` entry point here. Each component is an independent, self-contained class.

## Commands

```bash
hatch test --cover        # run the test suite with coverage (canonical, per README)
hatch fmt --check         # check formatting/lint (ruff 0.14.9, config in pyproject)
hatch run types:check     # pyright type check
hatch run types:stats     # pyright stats

pytest tests/test_AO3401A.py            # run a single test file
pytest tests/test_AO3401A.py -k ao3401a # run a single test
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

### Tests (`tests/`)
One `test_*.py` per component. Tests subclass `jitx.test.TestCase` (a `unittest.TestCase` that activates the JITX *instantiation context* in `setUpClass` — required so that JITX class members instantiate correctly; do not use plain `unittest.TestCase` for code that builds design elements). A test typically defines a `SampleDesign` subclass containing an `@inline class circuit(Circuit)` that instantiates the component, then asserts on the built design.

## Dependencies & environment

Requires Python ≥3.12; the test matrix covers 3.12/3.13/3.14. Built with hatchling + hatch-vcs (version derived from git tags). Core deps: `jitx` (4.x), `jitxlib-standard`, `jitxlib-parts`, `jitxlib-voltage-divider`, `eseries`. The wheel packages only `src/jitxexamples`; `docs/` is excluded from both pyright and `[tool.jitx]`.
