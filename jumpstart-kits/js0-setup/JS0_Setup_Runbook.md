<!--
JITX Setup Runbook (JS0) · rev 1.2 · 2026-08-28
Paste this file into your AI coding agent (Claude Code, Codex / GPT, or Devin), or upload it,
and tell the agent to follow it.
-->

# JITX Setup Runbook (JS0)

**Goal (for the agent):** Get JITX installed, authenticated, skills-enabled, and validated, then close with a live design change so I see the design-as-code loop. Follow the steps **in order**. Where a step is marked **[HUMAN]**, stop and wait for me — do not proceed until I confirm.

> **[HUMAN] Claude Code users — run this from the terminal if you can.** The runbook works in the VSCode / Cursor extension, but with limitations, and the journey differs slightly there. The `/plugin` command doesn't exist in the extension, so the step-4 skills install has to go through the `claude` CLI — which isn't on the extension shell's `PATH` either, so you have to reach the binary the extension ships. None of that applies in a terminal.
>
> **If you're reading this in the extension, say so before step 1.** If I can switch, I'd rather start over with `claude` in a terminal. If I can't, keep going — step 4 spells out the extension route, and it's the only step that changes.

> **For humans:** manual (no-agent) steps and environment/IT prerequisites live in the **Reference Companion** — https://github.com/JITx-Inc/jitx-examples/blob/main/jumpstart-kits/js0-setup/JS0_Reference_Companion.md. See it if you have no AI agent, or you're in a locked-down environment.

> **Whose home is `~`?** I may be running you as a different OS user than the one I'm logged in as — a dedicated agent account, a container, a remote box. So where a path below could belong to either of us, it names the owner: `~<my-login>/…` is **my** desktop home, and a bare `~` is yours. If you can't read `~<my-login>`, say so rather than reporting the file missing.

**Assumptions / prerequisites**

- Python 3.12+ and `git` are available.
- You are running inside an AI coding agent that can execute shell commands (not sandboxed).
- (Optional) A code editor is installed (VSCode, Cursor, or Windsurf/Devin).

---

## Steps

**0 · Check prerequisites.**
Read this runbook's revision out of the HTML comment at the top of the file and tell me what it is, so the run is pinned to a known version of the kit. Then run `python3 --version` (must be 3.12 or newer) and `git --version`. Also check `uv --version` (optional). If Python is older than 3.12, **stop** and tell me how to install 3.12+ for my OS.

**1 · Install the JITX CLI** — the global bootstrap: it authenticates you and scaffolds projects.
Run `pip install jitx`. If it fails with the PEP 668 "externally-managed-environment" error — the Python packaging rule that stops `pip` writing into a system-managed interpreter — **stop and ask me whether it's ok to use uv instead**. If I say yes, install `uv` if it's missing (https://astral.sh/uv) and run `uv tool install jitx`. Verify with `jitx --version` (expect **4.4.0 or newer**) and tell me the version.

**2 · Install the runtime.**
Run `jitx runtime install`. Do this **before** signing in — `jitx auth login` needs the runtime present to work. **On Windows** this opens an MSI installer in a **separate popup window** (possibly behind others): stop and tell me to complete it — the command won't return until I do.

If it fails with `not tested on Linux distribution '<x>'`, retry as `jitx runtime install --target ubuntu` — the Ubuntu build runs on most glibc Linux. Verify with `jitx runtime introspect`, **not** `jitx runtime status`: `install`, `update` and `introspect` work anywhere, while `status`, `start` and `stop` are project-scoped and fail with `No pyproject.toml found` until step 5a creates a project.

**3 · [HUMAN] Authenticate.**
Run `jitx auth login 2>&1`. It prints an activation link and a code; I open the link in any browser, approve, and the command completes on its own. **The `2>&1` matters** — the link goes to stderr, so a shell that captures only stdout shows you nothing and no error. **On Windows**, tell me to run `jitx auth login` in my own terminal instead.

**The link expires in 10 minutes.** Show it to me the moment you have it, and if it expires before I approve, mint a new one and tell me — don't report the sign-in as failed.

If you still get no link, run it under a pty as a fallback — `script -q /dev/null jitx auth login` (macOS) or `script -qec "jitx auth login" /dev/null` (Linux) — which merges the two streams for you. If that shows nothing either, report the failure rather than retrying.

**Stop once the link is showing and let me finish the sign-in myself** — do **not** guess or enter my credentials. After I confirm, run `jitx auth show` to verify, then continue.

**4 · Enable the JITX skills.**
Enable the skills for whichever runtime you are:

- **Claude Code (terminal)** — `/plugin marketplace add JITx-Inc/jitx-skills`, then `/plugin install jitx-skills@jitx`.
- **Claude Code (VSCode / Cursor extension)** — `/plugin` isn't available there; it just answers `/plugin isn't available in this environment.` Use the CLI form instead:
  ```bash
  claude plugin marketplace add JITx-Inc/jitx-skills
  claude plugin install jitx-skills@jitx
  ```
  `claude` usually isn't on `PATH` in the extension's shell, but the extension ships its own binary at `~<my-login>/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude` (Cursor: `~<my-login>/.cursor/extensions/…`) — **my** home, not yours, because I installed the extension. Put that on `PATH` or call it by full path.

  Either way, invoke the base workflow with `/jitx-skills:jitx`.
- **Codex / GPT** — requires Codex CLI 0.142.0 or newer. Run `codex plugin marketplace add JITx-Inc/jitx-skills`, then `codex plugin add jitx-skills@jitx`. Invoke skills with `$jitx …`.
- **Devin** — no global skills install today; the skills go **into a design repo**. So create the design project first (jump ahead to step **5a**'s `jitx project layout init`), then `git clone https://github.com/JITx-Inc/jitx-skills.git` and copy its `skills/*` into the design repo under `.agents/skills/`. Devin auto-discovers them (no re-index step); ask it to reload or list skills, or start a new session. Invoke with `@jitx <request to AI>`; sub-skill discovery from the base skill may not work, so name the specific sub-skill when the task matches one (e.g. `@jitx-component-modeler <request to AI>`).

**[HUMAN] Verify the skills loaded. This is required — do not skip it or assume it worked.**
First, the part you can check yourself: your runtime's plugin list should show the bundle enabled (Claude Code: `claude plugin list` → `✔ enabled`). If it lists the plugin but reports `failed to load` with `Path not found` errors, run `claude plugin marketplace update jitx` — the cached marketplace is stale and still points at skills that have since been renamed or removed. Reinstalling the plugin does not fix that.

Then the part only I can do: a plugin install only takes effect after a restart, so ask me to start a **new** session, and confirm in that session that the base skill is both listed **and** actually invocable (`/jitx-skills:jitx`, `$jitx …`, or `@jitx …`, per your runtime).

**Don't attempt step 5's design work until this passes.** The skills are what teach you to open the schematic and board views and to write design code, so without them you can't finish 5a or 5b. If the skills aren't there, fix this step and re-verify; don't work around it. While I'm restarting my session you may go ahead and scaffold and build 5a — that part needs no skills.

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
- **5b — Full build.** Clone `https://github.com/JITx-Inc/jitx-examples`, run the setup commands above, and **take the `si_bga_optimization` target verbatim from `jitx find`** — the same rule as 5a, so a repo reorganisation can't strand you on a stale module path. Expect `jitxexamples.demos.si_bga_optimization.bga_escape.bga_optimization_design`. Build it, confirm it builds, and display the board UI windows for me.

> **If a build fails with "You are not authenticated. Please sign in through the JITX Sidebar in VSCode"**, that means step 3 didn't complete — re-run `jitx auth login`, don't go looking for VSCode. `jitx runtime start --background` succeeds while unauthenticated, so a green step 2 is not proof of sign-in, and the real one-line cause arrives underneath two Python tracebacks.

> **Opening the views — what to expect.**
>
> - **The first window may be slow.** The very first board or schematic view in 5a can take a few minutes to appear — more likely on macOS. If it doesn't come up straight away, wait for it and tell me it's coming — do **not** re-run the command or report it broken. If nothing has appeared after **5 minutes**, tell me. Any later view, 5b's included, comes up faster.
> - **`jitx ui open` blocks while its window is open**, so launch it in the background rather than letting it hang your shell for the whole session. Later calls return immediately and add their windows to the JITX app already running — there's no limit on how many views can be open at once, so leave 5a's windows up while you open 5b's.

Report the results of both builds.

**6 · (Optional) Guide installation of the editor JITX plugin.**
Search the editor's (or VSCode's) marketplace for the JITX extension and install it via that editor's CLI. Ask me to confirm it's installed and its sidebar shows me authenticated.

**7 · [HUMAN] Close the loop — make a live design change.**
Now show me the design-as-code loop on the step-5 design. **Invite me to make a change**, then **wait for me to ask.** Report the before → after values. If the view doesn't redraw after the rebuild, reopen it — see step 5's note on how `jitx ui open` behaves.

- **If 5b ran** — tell me I can adjust the differential-pair geometry; suggest I say: *"change the differential-pair trace width to 0.0762 mm and the pair spacing to 0.1568 mm."* Edit the constants — `DIFFPAIR_TRACE_WIDTH` → `0.0762` and `DIFFPAIR_PAIR_SPACING` → `0.1568` (in the design's `substrate.py`) — rebuild, and show me **both** the changed source lines and the updated board view. Say plainly what the edit costs: those constants are the 85 Ω stripline geometry, so the new values detune every 85 Ω signal layer. We're changing them to watch a source edit reach the board, and in real work you'd re-solve the geometry for the impedance target. **Then point me at the right layer** — select `L2-Signal1` and zoom into the BGA escape region, where the diff-pair geometry lives. The change is subtle but visible there; it won't show on the default `L1-Ground1` whole-board view.
- **If 5b didn't build** — fall back to the 5a design: tell me I can change a resistor value, and suggest I say *"change r2 to 10 kΩ."* Edit that resistor's `resistance` in the project's `main.py`, rebuild, and show me the changed line and the updated schematic. Say which design you used.

---

## Done when

- `jitx --version` is 4.4.0 or newer and `jitx auth show` confirms I'm authenticated.
- The JITX skills are visible **and invocable** in a new agent session, confirmed by actually invoking one.
- **5a** (two-resistor template) builds, and so does **5b** (`si_bga_optimization`).
- A prompted design change — the diff-pair edit on 5b, or a resistor value on 5a if 5b didn't build — is applied, rebuilt, and visible in both the code and the UI.
