# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

## Read README.md first

`README.md` is the single source of truth for what this repo is, its layout, the commands, and the
demo build target. Read it — do not restate it here. This file holds only the things that are
specifically about working *with an agent* in this repo.

## Repo-specific rules

- **`designs/` at the repo root is JITX build output, not source.** `jitx design build` creates
  `<repo-root>/designs/<module.path.design_name>/` (`design-info/`, `temp/`, ...). That name is
  chosen by JITX. The Python demo sources live in `src/jitxexamples/demos/` for exactly this reason.
  Never add source under a root `designs/`, and never rename `demos/` back to `designs/`.

- **Tests must subclass `jitx.test.TestCase`, never plain `unittest.TestCase`.**
  `jitx.test.TestCase.setUpClass` activates the JITX *instantiation context*; without it, JITX class
  members are not instantiated and assertions silently operate on placeholder objects rather than
  real design elements.

- **`jitx.test.TestCase` does not need the JITX runtime.** It only activates the instantiation
  context, so instantiating a `SampleDesign` works offline. Only `jitx design build` / `jitx ui` need
  `jitx runtime start`; `jitx design build --dry <target>` translates a design without one.

- **The repo targets the jitx 4.6 line.** `pyproject.toml` requires `jitx>=4.6.0rc2,<4.7` and
  `jitxlib-standard>=4.6.0rc2,<4.7`. The cap matters: the floor is a pre-release, so without it a
  resolve on the internal index takes the newest pre-release, a 4.7 alpha. Two surfaces have to
  agree (a 4.6 package against a 4.5 runtime is not a working install), so `jitx design build` also
  needs the runtime (`~/.jitx/current`, check with `jitx runtime introspect`) on the same line as
  the library. Before concluding demo code is broken, check which `jitx` you actually resolved on
  both. When jitx 4.7.0 is released, raise both caps and rerun the suite: left in place, the cap
  makes pip downgrade a 4.7 project's jitx or fall back to an older `jitxexamples`.

- **A maintainer machine does not resolve what a customer resolves.** Developer setups here carry an
  internal index and a pre-release opt-in, and they are not all environment variables —
  `~/.pip/pip.conf` can set `extra-index-url` and `pre = true`, which `env -u PIP_EXTRA_INDEX_URL`
  does not strip. To reproduce a customer's resolution, neutralise the config file as well:

  ```bash
  env -u PIP_PRE -u PIP_EXTRA_INDEX_URL -u UV_PRERELEASE -u UV_EXTRA_INDEX_URL \
    PIP_CONFIG_FILE=/dev/null hatch test --cover
  ```

  Confirm what you got (`pip list | grep jitx`) rather than assuming. While the floors in
  `pyproject.toml` are pre-releases that public PyPI does not carry, an isolated resolve fails
  outright; once they are public releases, a `.dev`, `a` or `rc` suffix means the isolation did not
  hold. Without it the `hatch` envs resolve *ahead* of the public line.

- **Parts tests resolve through the project's parts chain.** `[tool.jitx.parts]` in
  `pyproject.toml` names `src/jitxexamples/parts/example-passives.csv` followed by `ideal`. Tests that resolve
  passives subclass `tests/parts.py:PartsTestDesign`, which loads that same chain from the project
  its own file sits in (so pytest can start from any directory) and disables locking.
  In a build, `ideal` needs the value pinned to one number, snaps it to E24, honors `case` and
  `tolerance` (0402 where no case is pinned, 1% where no tolerance is), and ignores every other filter
  (`mounting`, `type`, a rating, a dielectric, a current or a frequency), so a rated query the CSV
  cannot meet resolves to an `IDEAL-*` part with no rating. `PartsTestDesign` swaps in
  `PlainValueIdeal`, which declines any query carrying such a filter, so in tests that query fails
  and a gap in the CSV cannot pass silently. A passing test still does not mean every part is
  orderable: plain value, case and tolerance queries the CSV cannot answer get `IDEAL-*` parts.
  A query `ideal` declines (an exact non-E24 value such as 30.9 kohm, a value range, or a tolerance
  limit under 1%) needs a real part in the CSV. `tests/test_parts_chain.py` checks the chain order,
  that the CSV answers before `ideal`, that a rated query fails rather than falling to `ideal`,
  and the CSV's tolerance and unit format. Do not add tests that require live parts-source access.

- **`src/jitxexamples/` is an implicit namespace package** (no `__init__.py`). Some `components/*`
  subdirectories have an empty `__init__.py` and some do not. That inconsistency is known and
  intentionally untouched — do not "fix" it as a drive-by.

- **This repo is publicly mirrored** to `JITx-Inc/jitx-examples` on release
  (`.github/workflows/mirror-main.yml` archives everything tracked except `.github/`). Keep
  comments, docs, and placeholder text customer-appropriate.

- **Every tracked file reaches a deployment surface; there is no maintainer-only tree.** Three
  surfaces publish out of this repo and all three work from tracked files: the sdist, the public
  mirror, and docs.jitx.com, which only ever extracts `jumpstart-kits/` out of that sdist. Keep
  kit specs and program TODOs out of the repo; git history holds the ones that used to be here.
  The sdist's `exclude = ["internal"]` and the mirror's `rm -rf "$MIRROR/internal"` stay as guards
  in case such a tree is added again. A file placed in `jumpstart-kits/` **publishes**: there is
  no per-file opt-out, because the docs build's `exclude_patterns` is empty by contract. After
  touching the sdist config, verify: `hatch build -t sdist`, then
  `tar tzf dist/jitxexamples-*.tar.gz` must list one `jumpstart-kits/` entry per tracked file under
  `jumpstart-kits/` (26 today) and no `internal` entry.

- **Kits carry no presentation decks.** The JS0 and JS1 decks and their deck tooling were
  removed on 2026-10-22; a kit is its README pages, runbooks, reference companions and supplied
  inputs. `git log -- internal/deck-tooling` recovers the old tooling from history.

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
