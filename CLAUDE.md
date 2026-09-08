# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

## Read README.md first

`README.md` is the single source of truth for what this repo is, its layout, the commands, and the
demo build target. Read it — do not restate it here. This file holds only the things that are
specifically about working *with an agent* in this repo.

## Repo-specific rules

- **`designs/` at the repo root is JITX build output, not source.** `jitx build` creates
  `<repo-root>/designs/<module.path.design_name>/` (`design-info/`, `temp/`, ...). That name is
  chosen by JITX. The Python demo sources live in `src/jitxexamples/demos/` for exactly this reason.
  Never add source under a root `designs/`, and never rename `demos/` back to `designs/`.

- **Tests must subclass `jitx.test.TestCase`, never plain `unittest.TestCase`.**
  `jitx.test.TestCase.setUpClass` activates the JITX *instantiation context*; without it, JITX class
  members are not instantiated and assertions silently operate on placeholder objects rather than
  real design elements.

- **`jitx.test.TestCase` does not need the JITX runtime.** It only activates the instantiation
  context, so instantiating a `SampleDesign` works offline. Only `jitx build` / `jitx ui` need
  `jitx runtime start`; `jitx build --dry <target>` translates a design without one.

- **JITX 4.4.0 is public, and the parked-changes list is `internal/JITX-4.4-RELEASE-ACTIONS.md`.**
  Read it before planning work here: it says what is already done so you don't redo it, and what is
  still open. Two items were still open as of 2026-08-31 — deleting
  `vishay_crcw._STANDARD_TABLE_OVERRIDES` (its trigger fired long ago) and regenerating
  `JS0_Environment_Setup.md` Appendix A, whose dependency table is still a 4.2-line snapshot. The
  file's runtime-surface check (`jitx runtime introspect` reporting a 4.4.x `release` build) had not
  been run at that point either.

- **The repo targets the jitx 4.4 line, and public PyPI now serves it.** `pyproject.toml` requires
  `jitx>=4.4.0,<5`, which resolves from public PyPI — the pre-release specifier and the
  CI-can't-install caveat are both gone. The `hatch` envs still add the internal index
  (`PIP_EXTRA_INDEX_URL`), so they resolve *ahead* of the public line: expect a `4.4.x.devN` build
  there rather than 4.4.0 exactly. Before concluding that demo code is broken, check which `jitx`
  you resolved, and note that `jitx build` also needs the runtime (`~/.jitx/current`) on the same
  line as the library.

- **The parts database is mocked in tests.** `tests/conftest.py` installs an autouse fixture
  patching `jitxlib.parts.query_api.dbquery` with fixtures from `captured_json/` and sets
  `JITX_MOCK_PARTS_DB=1`. Do not add tests that require live parts-DB access.

- **`src/jitxexamples/` is an implicit namespace package** (no `__init__.py`). Some `components/*`
  subdirectories have an empty `__init__.py` and some do not. That inconsistency is known and
  intentionally untouched — do not "fix" it as a drive-by.

- **This repo is publicly mirrored** to `JITx-Inc/jitx-examples` on release
  (`.github/workflows/mirror-main.yml` archives everything tracked except `.github/` and
  `internal/`). Keep comments, docs, and placeholder text customer-appropriate.

- **`internal/` is tracked but reaches no deployment surface.** It holds the JumpStart Kit specs,
  program TODOs, and deck-production tooling that used to live in the now-deprecated
  `JITx-Inc/jumpstart-kits`. Three surfaces publish out of this repo and all three work from tracked
  files, so each excludes `internal/` explicitly: the sdist via
  `[tool.hatch.build.targets.sdist] exclude`, the public mirror via `rm -rf "$MIRROR/internal"`, and
  docs.jitx.com by only ever extracting `jumpstart-kits/` out of that sdist. Moving a file from
  `internal/` into `jumpstart-kits/` **publishes it** — there is no per-file opt-out, because the
  docs build's `exclude_patterns` is empty by contract. After touching the sdist config, verify both
  directions: `tar tzf dist/jitxexamples-*.tar.gz` must list 28 `jumpstart-kits/` entries and no
  `internal/` ones.

- **The committed kit decks are generated; don't hand-edit the `.pptx`.**
  `internal/deck-tooling/` holds the build scripts, and each writes straight into the kit directory
  that publishes it — `jumpstart-kits/js0-setup/presentation/` for JS0, and the per-part directory
  `jumpstart-kits/js1-stackup-components/part<N>-<slug>/` for each JS1 part. All four are on the
  JITX brand (black, Arial, teal
  `#01BFA5` / amber `#FEC107`, `jitX` mark on every slide) — see
  `internal/deck-tooling/DESIGN-SYSTEM.md`. Neither generator is byte-deterministic, so verify a
  rebuild with `internal/deck-tooling/deck_text.py`, which diffs slide text and speaker notes; a
  restyle should leave that diff empty. Two earlier decks *were* patched at the XML level after
  generation, which silently made their scripts unable to reproduce them — hence the rule.

- **Merge a `develop` → `main` release PR with "Create a merge commit", never "Squash and merge".**
  Feature PRs into `develop` are squashed as usual; the release PR is the exception. Squashing
  `develop` onto `main` collapses its history into one commit and erases the ancestry link, so git
  falls back to a stale merge base and the *next* release PR reports every file both branches
  touched as a spurious add/add conflict. Resolving those by hand also silently resurrects files
  `develop` deliberately renamed or deleted, which is the trap — the conflicts look real.

- **If a release ever does land on `main` as a squash, sync it back before opening the next one.**
  Compare `git rev-parse origin/main^{tree}` against the tree of the `develop` commit that was
  squashed. If the two OIDs match, `main` holds nothing `develop` lacks, so
  `git merge -s ours origin/main` restores the ancestry without touching content; confirm with
  `git diff --quiet origin/develop HEAD` before pushing. If the OIDs *differ*, something landed on
  `main` directly — do a normal merge and resolve it for real.

## Verification

Run the commands in README.md's Commands section. Do not invent alternatives:
`hatch test --cover`, `hatch fmt --check`, `hatch run types:check`.

Note that the `pre-commit` hook is **not installed by default** (`core.hooksPath` is unset), and it
invokes bare `python`, which may not be on PATH. Never treat a successful commit as evidence that
the tests passed — run `hatch test --cover` explicitly.
