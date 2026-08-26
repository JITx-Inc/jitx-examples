<!--
JITX Setup Runbook (JS0)
Paste this file into your AI coding agent (Claude Code, Codex / GPT, or Devin), or upload it,
and tell the agent to follow it.
-->

# JITX Setup Runbook (JS0)

**Goal (for the agent):** Get JITX installed, authenticated, skills-enabled, and validated, then close with a live design change so I see the design-as-code loop. Follow the steps **in order**. Where a step is marked **[HUMAN]**, stop and wait for me — do not proceed until I confirm.

> **[HUMAN] Claude Code users — run this from the terminal if you can.** The runbook works in the VSCode / Cursor extension, but with limitations, and the journey differs slightly there. The `/plugin` command doesn't exist in the extension, so the step-4 skills install has to go through the `claude` CLI — which isn't on the extension shell's `PATH` either, so you have to reach the binary the extension ships. None of that applies in a terminal.
>
> **If you're reading this in the extension, say so before step 1.** If I can switch, I'd rather start over with `claude` in a terminal. If I can't, keep going — step 4 spells out the extension route, and it's the only step that changes.

> **For humans:** manual (no-agent) steps and environment/IT prerequisites live in the **Reference Companion**. See it if you have no AI agent, or you're in a locked-down environment.

**Assumptions / prerequisites**

- Python 3.12+ and `git` are available.
- You are running inside an AI coding agent that can execute shell commands (not sandboxed).
- (Optional) A code editor is installed (VSCode, Cursor, or Windsurf/Devin).

---

## Steps

**0 · Check prerequisites.**
Run `python3 --version` (must be 3.12 or newer) and `git --version`. Also check `uv --version` (optional). If Python is older than 3.12, **stop** and tell me how to install 3.12+ for my OS.

**1 · Install the JITX CLI** — the global bootstrap: it authenticates you and scaffolds projects.
Run `pip install jitx`. If it fails with the PEP 668 "externally-managed-environment" error — the Python packaging rule that stops `pip` writing into a system-managed interpreter — **stop and ask me whether it's ok to use uv instead**. If I say yes, install `uv` if it's missing (https://astral.sh/uv) and run `uv tool install jitx`. Verify with `jitx --version` (expect **4.2.2 or newer**) and tell me the version — step **5b** runs only on 4.2.x.

**2 · Install the runtime.**
Run `jitx runtime install`. Do this **before** signing in — `jitx auth login` needs the runtime present to work. **On Windows** this opens an MSI installer in a **separate popup window** (possibly behind others): stop and tell me to complete it — the command won't return until I do.

**3 · [HUMAN] Authenticate.**
`jitx auth login` prints an activation link and waits for me to approve it. It prints **nothing at all** when its output isn't a terminal — the normal case for an agent — so run it under a pty (pseudo-terminal, which makes the command believe it's attached to a real terminal) and show me the link:

- **macOS** — `script -q /dev/null jitx auth login`
- **Linux** — `script -qec "jitx auth login" /dev/null`
- **Windows** — there's no `script`; tell me to run `jitx auth login` in my own terminal instead.

If you get no link and no error, you ran it without a pty — retry with the wrapper above rather than reporting success. **Stop once the link is showing and let me finish the sign-in myself** — do **not** guess or enter my credentials. After I confirm, run `jitx auth show` to verify, then continue.

**4 · Enable the JITX skills.**
Enable the skills for whichever runtime you are:

- **Claude Code (terminal)** — `/plugin marketplace add JITx-Inc/jitx-skills`, then `/plugin install jitx-skills@jitx`.
- **Claude Code (VSCode / Cursor extension)** — `/plugin` isn't available there; it just answers `/plugin isn't available in this environment.` Use the CLI form instead:
  ```bash
  claude plugin marketplace add JITx-Inc/jitx-skills
  claude plugin install jitx-skills@jitx
  ```
  `claude` usually isn't on `PATH` in the extension's shell, but the extension ships its own binary at `~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude` (Cursor: `~/.cursor/extensions/…`). Put that on `PATH` or call it by full path.

  Either way, invoke the base workflow with `/jitx-skills:jitx`.
- **Codex / GPT** — requires Codex CLI 0.142.0 or newer. Run `codex plugin marketplace add JITx-Inc/jitx-skills`, then `codex plugin add jitx-skills@jitx`. Invoke skills with `$jitx …`.
- **Devin** — no global skills install today; the skills go **into a design repo**. So create the design project first (jump ahead to step **5a**'s `jitx project layout init`), then `git clone https://github.com/JITx-Inc/jitx-skills.git` and copy its `skills/*` into the design repo under `.agents/skills/`. Devin auto-discovers them (no re-index step); ask it to reload or list skills, or start a new session. Invoke with `@jitx <request to AI>`; sub-skill discovery from the base skill may not work, so name the specific sub-skill when the task matches one (e.g. `@jitx-component-modeler <request to AI>`).

**[HUMAN] Verify the skills loaded. This is required — do not skip it or assume it worked.**
A plugin install only takes effect after a restart, so ask me to start a **new** session, then confirm in that session that the base skill is both listed **and** actually invocable (`/jitx-skills:jitx`, `$jitx …`, or `@jitx …`, per your runtime).

**Do not begin step 5 until this passes.** 5a and 5b depend on the skills — they are what teach you how to open the schematic and board views, so without them you cannot finish either build. If the skills aren't there, fix this step and re-verify; don't work around it.

**5 · Validate with two builds.**
Drive these with the base JITX skill (step 4). The step-1 CLI has no `pip`, so run the setup commands below inside each project after it has been created.

```bash
# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate

# Windows (PowerShell)
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
```

```bash
pip install jitx
jitx project dependencies upgrade
jitx runtime start --background
jitx find
```

- **5a — Simplest build.** Run `jitx project layout init` to create a new JITX project seeded with a two-resistor sample design (Devin users: you made this project in step 4). Then run the setup commands above and build the seeded non-test target from `jitx find` — ignore any target whose module path comes from `test`, `tests`, or a test file. **Take the target verbatim from `jitx find`** — the scaffold names the seeded design class after the project directory, lowercased with hyphens and spaces turned into underscores, so a directory called `my-first-board` builds as `jitx build my_first_board.main.my_first_board`. Then show me the schematic and board views.
- **5b — Full build (JITX 4.2.x only).** If step 1's `jitx --version` is **4.3 or newer, skip 5b** — `si_bga_optimization` still targets the 4.2 API and won't build; don't try to fix it. Otherwise clone `https://github.com/JITx-Inc/jitx-examples`, build the `si_bga_optimization` design (build target `jitxexamples.demos.si_bga_optimization.bga_escape.bga_optimization_design`), confirm it builds, and display the board UI windows for me.

> **Opening the views — what to expect.**
>
> - **The first window is slow.** The very first board or schematic view in 5a can take **3–4 minutes** to appear. Wait for it, and tell me it's coming — do **not** re-run the command or report it broken. If nothing has appeared after **5 minutes**, tell me. Every later view, 5b's included, comes up much faster.
> - **`jitx ui open` blocks while its window is open**, so launch it in the background rather than letting it hang your shell for the whole session. Later calls return immediately and add their windows to the JITX app already running — there's no limit on how many views can be open at once, so leave 5a's windows up while you open 5b's.

Report the results, saying plainly if 5b was skipped.

**6 · (Optional) Guide installation of the editor JITX plugin.**
Search the editor's (or VSCode's) marketplace for the JITX extension and install it via that editor's CLI. Ask me to confirm it's installed and its sidebar shows me authenticated.

**7 · [HUMAN] Close the loop — make a live design change.**
Now show me the design-as-code loop on the step-5 design. **Invite me to make a change**, then **wait for me to ask.** Report the before → after values. If the view doesn't redraw after the rebuild, reopen it — see step 5's note on how `jitx ui open` behaves.

- **If 5b ran** — tell me I can adjust the differential-pair geometry; suggest I say: *"change the differential-pair trace width to 0.0762 mm and the pair spacing to 0.1568 mm."* Edit the constants — `DIFFPAIR_TRACE_WIDTH` → `0.0762` and `DIFFPAIR_PAIR_SPACING` → `0.1568` (in the design's `substrate.py`) — rebuild, and show me **both** the changed source lines and the updated board view. These two numbers are arbitrary demo values, not an impedance target: the point is to watch a source edit reach the board view, so success is "constants changed, build succeeded, view redrew."
- **If 5b was skipped** — use the 5a design instead: tell me I can change a resistor value, and suggest I say *"change r2 to 10 kΩ."* Edit that resistor's `resistance` in the project's `main.py`, rebuild, and show me the changed line and the updated schematic.

---

## Done when

- `jitx --version` is 4.2.2 or newer and `jitx auth show` confirms I'm authenticated.
- The JITX skills are visible **and invocable** in a new agent session, confirmed by actually invoking one.
- **5a** (two-resistor template) builds, and so does **5b** (`si_bga_optimization`) unless it was skipped because JITX is 4.3+.
- A prompted design change — the diff-pair edit on 5b, or a resistor value on 5a if 5b was skipped — is applied, rebuilt, and visible in both the code and the UI.
