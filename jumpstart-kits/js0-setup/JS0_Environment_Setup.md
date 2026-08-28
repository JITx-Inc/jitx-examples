# JS0 — Environment Setup

Preparing a machine to run JITX, for **[IT/Admin]** and **[Engineer]** readers. Work through this
alongside the [Setup Runbook](JS0_Setup_Runbook.md); the runbook drives the install, this document
covers what has to be true around it.

Machine sizing, network egress, deployment architecture, licensing models, and data handling are in
the [JITX Architecture and Systems Requirements](../shared/JITX_Architecture_and_Systems_Requirements_v2_0.md).
Start there when preparing a locked-down or enterprise-managed machine, or before a pilot or
rollout. This document adds the pieces that sit on top of it: source trust, the AI skills, and a
readiness checklist.

---

## 1. Package and extension trust **[IT/Admin]**

Security policy interacts with every requirement in the architecture document. Address these
alongside the network allowlisting.

**Package source trust.** Internal package mirrors must carry the JITX Python packages and serve
them with valid certificates. TLS-inspecting proxies sometimes break `pip` / `uv` certificate
validation — if installs fail with SSL errors, your security team needs to trust the proxy's CA in
the environment or exempt the package endpoints.

**Extension and runtime trust.** Endpoint-protection and application-allowlisting policies can block
the JITX runtime binary or the editor extension from installing or executing. Confirm both are
permitted to install and run.

Install locations differ by platform: per-user on macOS and Linux, but split on Windows — the binary
in `\Program Files (x86)`, configuration in the user directory, and the binary install may require
administrator privilege. **An allowlist written only against per-user paths will miss the Windows
binary.** Your JITX contact can confirm exact paths if your policy needs them.

---

## 2. The AI skills (the largest hurdle)

JITX designs are expressed as Python code, and the intended workflow is for an **AI assistant to
write that code** with the engineer directing and reviewing it. Standing up a capable assistant in
the customer's environment is, by a wide margin, the most involved part of enablement.

### The skills are required for competent output **[Engineer]**

Every model — whether a frontier model or one from your organization's approved list — needs the
**JITX skills** to write competent, JITX-compatible Python. The skills encode JITX's APIs,
conventions, and review gates so the model produces correct, idiomatic designs instead of
plausible-looking but incorrect code. **Enabling the skills in your AI environment is the key step.**

### Choosing a model **[IT/Admin + Engineer]**

Use a model from your organization's approved list — cloud-hosted or on-premises, whichever your
organization approves. JITX does not call model APIs directly: compatibility requires only that your
assistant can edit Python project files and invoke the `jitx` CLI.

### What the skills are

`jitx-skills` is a bundle of specialized skills covering the JITX design workflow — a base workflow
skill plus focused skills for component modeling from datasheets, circuit building, substrate and
stackup modeling, physical layout authoring, signal-integrity constraints, pin assignment,
same-model code review, and mechanical CAD interchange. The bundle is open and lives at
**`github.com/JITx-Inc/jitx-skills`**. The repository's `skills/<skill-name>/SKILL.md` files are the
source of truth; the same skill tree is packaged for several AI runtimes.

> The exact set of skills in the repository evolves. Treat the cloned repository as authoritative for
> which skills exist, and confirm the current list with your JITX contact rather than hard-coding it.

### Setup by AI runtime **[Engineer]**

The [Setup Runbook](JS0_Setup_Runbook.md) step 4 drives this interactively. The reference commands,
including updates and migration, are below.

Claude Code and Codex both install directly from GitHub and don't need a local clone. Devin does
need one, to copy the skill files into the repo it indexes:

```bash
git clone https://github.com/JITx-Inc/jitx-skills.git
```

The repo contains one shared `skills/` tree plus runtime-specific packaging:

- **Codex / GPT** — `.codex-plugin/plugin.json`, plus a root `.agents/plugins/marketplace.json` that makes the repo itself a Codex marketplace.
- **Claude-style plugin hosts** — `.claude-plugin/` (plugin manifest + marketplace listing).
- **Devin** — copy the shared skill directories into the repo Devin indexes, under `.agents/skills/`.

#### Claude Code

Both the terminal Claude Code and the VSCode / Cursor extension work. Where the choice is open,
**lean toward the terminal** — installs and updates are a single slash command there, while the
extension needs the CLI form plus a `PATH` fix-up to reach its bundled binary. It's a mild
preference, not a requirement; the extension is fine once the plugin is in place.

Add the GitHub marketplace, then install the plugin. **In the terminal Claude Code**, use the slash
commands:

```text
/plugin marketplace add JITx-Inc/jitx-skills
/plugin install jitx-skills@jitx
```

**In the VSCode or Cursor extension**, `/plugin` isn't available — it answers `/plugin isn't
available in this environment.` Use the equivalent CLI commands instead:

```bash
claude plugin marketplace add JITx-Inc/jitx-skills
claude plugin install jitx-skills@jitx
```

`claude` is typically not on `PATH` in the extension's shell. The extension ships its own binary in
the engineer's home, at `~<engineer-login>/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude`
(Cursor: `~<engineer-login>/.cursor/extensions/…`) — put that directory on `PATH`, or invoke the
binary by full path. Name the login rather than writing a bare `~`, which resolves elsewhere for an
agent running under its own OS account.

Skills are namespaced under the plugin name — invoke the base workflow with `/jitx-skills:jitx`.

To update later, refresh the marketplace and then the plugin — `/plugin marketplace update jitx`
(extension: `claude plugin marketplace update jitx`), then `claude plugin update jitx-skills@jitx`.
Auto-update is off by default for third-party marketplaces; opt in through the interactive `/plugin`
manager, which is also where you can update from inside the terminal Claude Code.

> If you previously added this marketplace under the old `jitx-skills` name, migrate with
> `/plugin marketplace remove jitx-skills` (CLI: `claude plugin marketplace remove jitx-skills`),
> then re-add it and reinstall using the commands above.

#### Codex / GPT

Requires **Codex CLI 0.142.0 or newer** — the version at which `codex plugin` gained the marketplace
commands below. The repo ships its own Codex marketplace manifest, so Codex installs straight from
GitHub the same way Claude Code does:

```bash
codex plugin marketplace add JITx-Inc/jitx-skills
codex plugin add jitx-skills@jitx
```

Restart Codex or start a new thread after installing. Invoke the skills explicitly, for example:

```text
$jitx build this design
$jitx-component-modeler create a component from this datasheet
$jitx-code-review review this JITX code
```

To update the Codex install:

```bash
codex plugin marketplace upgrade jitx
codex plugin add jitx-skills@jitx
```

Then restart Codex or start a new thread.

#### Devin

Devin does not consume the Codex plugin manifest directly, and it has no global skills installation
today — the skills are installed **into a design repo**. That means the design project must exist
first: create your JITX design project (e.g. with `jitx project layout init`), then put the skill
folders in that repository:

```bash
cd /path/to/design-repo
mkdir -p .agents/skills
cp -R /path/to/jitx-skills/skills/* .agents/skills/
```

If the design repo is git-backed, commit and push the added files so Devin's indexed copy sees them:

```bash
git add .agents/skills
git commit -m "Install JITX skills for Devin"
git push
```

Devin auto-discovers `SKILL.md` files in the repo — there's no manual re-index step. Start a new
Devin session (or ask it to reload/list skills) and verify with:

```text
List the available skills related to JITX. Confirm whether you can see @jitx,
@jitx-component-modeler, @jitx-circuit-builder, @jitx-substrate-modeler,
@jitx-physical-layout, @jitx-interconnect-constraints, @jitx-pin-assignment,
@jitx-code-review, and @jitx-mechanical.
```

Invoke the narrowest relevant skill explicitly — Devin may not route from the base `@jitx` skill to
the right sub-skill on its own, so name the sub-skill directly when the task matches one (fall back
to `@jitx <request to AI>` for general work). For example:

```text
@jitx-component-modeler Create a JITX component from this datasheet.
@jitx-circuit-builder Wire this regulator application circuit.
@jitx-code-review Review this JITX design code.
```

### Notes on the skills

- Keep `skills/<skill-name>/SKILL.md` as the shared source of truth across runtimes.
- The Codex plugin packaging is for Codex; Devin uses the checked-in `.agents/skills`.
- **Keep JITX core and skills in step.** Running an upgraded JITX core against an old skills bundle (or vice versa) produces version-mismatch failures that surface as confusing errors during a session. Update both together.

---

## 3. Consolidated readiness checklist

**Machine**

- [ ] Supported OS: Windows, macOS, or Linux **[Engineer]**
- [ ] Adequate RAM (16–32 GB routine; 64–128 GB for large designs) **[IT/Admin + Engineer]**
- [ ] Heap variables raised for large designs (see [Appendix B](#appendix-b--memory-configuration-for-large-designs)) **[Engineer]**
- [ ] Sufficient free disk and a modern multi-core CPU **[Engineer]**

**Software and tooling**

- [ ] VSCode (or Cursor / Windsurf / Devin) installed **[Engineer]**
- [ ] Python 3.12+ available to the editor **[Engineer]**
- [ ] JITX extension installed (pulls in JITX packages + runtime) **[IT/Admin + Engineer]**
- [ ] First project created successfully **[Engineer]**

**Network (outbound HTTPS, direct or via approved proxy/mirror)**

- [ ] PyPI (`pypi.org`, `files.pythonhosted.org`) or internal mirror **[IT/Admin]**
- [ ] Editor extension marketplace **[IT/Admin]**
- [ ] JITX backend / runtime artifacts (`*.jitx.com`) **[IT/Admin]**
- [ ] GitHub (`github.com/JITx-Inc/jitx-skills`) **[IT/Admin]**
- [ ] Local firewall permits TCP connections to `localhost` (editor-to-runtime) **[IT/Admin]**

**Security**

- [ ] Package source trusted; TLS-inspection CA handled **[IT/Admin]**
- [ ] Extension and runtime permitted by endpoint protection, including the Windows `\Program Files (x86)` binary **[IT/Admin]**
- [ ] AI assistant and data-handling approach approved **[IT/Admin]**
- [ ] Licensing endpoint reachable for license refresh, or an air-gapped/node-locked license file arranged **[IT/Admin + Engineer]**

**AI**

- [ ] AI model chosen from the approved list **[IT/Admin + Engineer]**
- [ ] `jitx-skills` installed in the chosen runtime (cloned first for Devin) **[Engineer]**
- [ ] Skills verified visible and invocable in a new session **[Engineer]**
- [ ] JITX core and skills versions kept in step **[Engineer]**

---

## Appendix A — Python dependencies

Creating a project installs the packages below into the project virtual environment. The JS kits
require **JITX 4.4.0 or newer** — a minimum JITX sets for these kits, not one derived from the table
below. The floor above is the number that matters. The table is only an **illustrative snapshot of
the shape of the dependency set** — it was taken on an earlier release and its versions are **not**
the floor; regenerate it for the version you are deploying with `pip list` in the project venv.
Confirm the current supported minimum with your JITX contact rather than relying on this document.

> Note: the JITX runtime version and the Python package versions do not track one-to-one — the
> `jitx` and `jitxcore` packages report their own version numbers. Expect them to differ from the
> runtime version; the two are versioned independently.

| Package | Version |
| --- | --- |
| annotated-doc | 0.0.5 |
| anyio | 4.14.2 |
| black | 25.1.0 |
| certifi | 2026.7.22 |
| click | 8.4.2 |
| dataclasses-json | 0.6.7 |
| docopt | 0.6.2 |
| docopt-subcommands | 4.0.0 |
| eseries | 1.2.1 |
| flexcache | 0.3 |
| flexparser | 0.4 |
| future | 1.0.0 |
| h11 | 0.16.0 |
| httpcore | 1.0.9 |
| httpx | 0.28.1 |
| idna | 3.18 |
| jitx | 4.2.2 |
| jitxcore | 4.2.0 |
| jitxexamples-components | 1.2.0 |
| jitxlib-parts | 1.2.0 |
| jitxlib-standard | 4.2.0 |
| jitxlib-voltage-divider | 1.1.0 |
| markdown-it-py | 4.2.0 |
| marshmallow | 3.26.2 |
| mdurl | 0.1.2 |
| mypy_extensions | 1.1.0 |
| numpy | 2.5.1 |
| packaging | 25.0 |
| pathspec | 1.1.1 |
| Pint | 0.24.4 |
| pip | 26.1.2 |
| platformdirs | 4.11.0 |
| protobuf | 7.35.1 |
| psutil | 7.2.2 |
| Pygments | 2.20.0 |
| rich | 15.0.0 |
| shapely | 2.1.2 |
| shellingham | 1.5.4 |
| typer | 0.25.1 |
| typing-inspect | 0.9.0 |
| typing_extensions | 4.16.0 |
| websockets | 15.0.1 |

---

## Appendix B — Memory configuration for large designs

JITX holds the design in memory. Large designs (many pins or high layer count) can need more heap
than the defaults. Two environment variables control it: set `JITX_INTERACTIVE_MAX_HEAP_SIZE` to the
GB you want to give JITX, and `STANZA_MAX_HEAP_SIZE` to about half of that. Allocate only what the
machine physically has — typical values are 32, 64, or 128 GB.

**Test it temporarily** (set the variables, then launch the editor from the same shell):

- *Windows (PowerShell):*

  ```powershell
  $env:JITX_INTERACTIVE_MAX_HEAP_SIZE = "32"; $env:STANZA_MAX_HEAP_SIZE = "16"; & "C:\Program Files\Microsoft VS Code\code.exe" .
  ```

- *macOS / Linux:*

  ```bash
  export JITX_INTERACTIVE_MAX_HEAP_SIZE=32
  export STANZA_MAX_HEAP_SIZE=16
  code .
  ```

**Make it permanent** once the larger heap is confirmed to help:

- *Windows:* Start → "Edit the system environment variables" → **Environment Variables** → under **System variables**, add `JITX_INTERACTIVE_MAX_HEAP_SIZE` and `STANZA_MAX_HEAP_SIZE`. Restart the terminal.
- *macOS / Linux:* add the two `export` lines to your shell profile (`~/.zshrc`, `~/.bashrc`, or `~/.bash_profile`), then `source` it.

**Verify on a running process:**

- *Windows:* open [Process Explorer](https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer), select the VSCode/JITX process → **Properties → Environment**.
- *macOS / Linux:* `ps eww <PID>` (find the PID with `ps aux | grep code`).

---

## References

- [JITX Architecture and Systems Requirements](../shared/JITX_Architecture_and_Systems_Requirements_v2_0.md) — deployment architecture, network egress, machine sizing, licensing models, and data handling.
- **JITX Memory Usage Application Note** — full treatment of heap-size configuration for large designs (the quick procedure is in [Appendix B](#appendix-b--memory-configuration-for-large-designs)).
- **JITX Skills repository** — `https://github.com/JITx-Inc/jitx-skills` (source of truth for the AI skills; clone for the current skill list and per-runtime packaging).

---

*Document the specific endpoints, mirror URLs, and approved AI model for each customer alongside this
note, and confirm the current package and skills list with your JITX contact before finalizing the
environment.*
