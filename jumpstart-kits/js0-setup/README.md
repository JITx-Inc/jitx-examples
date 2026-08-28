# JS0 — Setup and Environment Validation

**Shortcut:** [JS0_Setup_Runbook.md](JS0_Setup_Runbook.md) —
{download}`download it <JS0_Setup_Runbook.md>`, hand it to your AI coding agent, and tell it to
follow the file. That one file runs the whole setup and validates it, stopping at the `[HUMAN]`
steps that need you. Everything below is the context around it.

Takes you from scratch to a configured, authenticated, skills-enabled JITX environment — proven by
two real builds and a closing design-as-code change. Work through JS0 before JS1.

Requires JITX 4.4.0 or newer.

## Start here — the JS0 walkthrough

You can get oriented by reading this page or alternatively downloading the 5-slide deck.
Instruction content is also available as a PDF or PPTX for reference or distribution, from the
[Presentation](presentation/) page:

- [JS0_Presentation.pdf](presentation/JS0_Presentation.pdf) — read-only, opens anywhere
- [JS0_Presentation.pptx](presentation/JS0_Presentation.pptx) — editable PowerPoint

### The goal — get JITX set up and AI-enabled correctly

You finish with the JITX CLI and runtime installed, an authenticated session, the JITX skills
enabled in your AI coding agent, successful builds, and one design change you make by prompting an
agent and then see the design change in the UI.

### The flow — six steps, two depend on you

Prereqs → Install + runtime → **Authenticate (you)** → Enable JITX skills → Validate → **Close the
loop (you)**

An AI agent runs these for you — Claude Code, Codex / GPT, or Devin — pausing twice: at sign-in,
where you enter your own credentials, and at the user-driven design change, which you prompt. No AI
agent? Run the same steps yourself from the [Reference Companion](JS0_Reference_Companion.md).

### Prove it works — two builds

1. **Simplest.** Create a new project and build the two-resistor template — the fast "it works."
2. **Full.** Build
   [`si_bga_optimization`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/demos/si_bga_optimization)
   from `jitx-examples`, the real toolchain exercise.

### Design as code — change one parameter, watch it rebuild

Builds successfully? Now change what you built. On `si_bga_optimization`, ask your agent to change
the differential-pair trace width to 0.0762 mm and the pair spacing to 0.1568 mm; on the template,
ask it to change a resistor value. It edits the design, rebuilds, and the view redraws.

> change the differential-pair trace width to 0.0762 mm and the pair spacing to 0.1568 mm

That one prompt moves `DIFFPAIR_TRACE_WIDTH` from 0.115 to 0.0762 mm and `DIFFPAIR_PAIR_SPACING`
from 0.118 to 0.1568 mm. That's the loop: prompt → code → build → see it. You're ready for JS1.

## Reference and Background Material

1. [Reference Companion](JS0_Reference_Companion.md) — the manual path, for when you have no agent:
   the same commands resequenced to run by hand, with the JITX skills enabled last. On a locked-down
   or enterprise-managed machine it points on to Environment Setup and the architecture doc rather
   than covering them itself. {download}`Download it <JS0_Reference_Companion.md>` to carry onto a
   machine with no browser or no egress.
2. [Environment Setup](JS0_Environment_Setup.md) — the reference for preparing a machine: package
   and extension trust, the AI skills and how to install them per runtime, and a consolidated
   **[IT/Admin]** / **[Engineer]** readiness checklist.
   {download}`Download it <JS0_Environment_Setup.md>`.
3. Preparing a managed or enterprise-locked machine? Read the
   [JITX Architecture and Systems Requirements](../shared/JITX_Architecture_and_Systems_Requirements_v2_0.md)
   before the runbook — deployment architecture, network egress, machine sizing, licensing models,
   and data handling.
