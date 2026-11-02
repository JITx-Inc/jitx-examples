# JS2: Circuit Construction

**Shortcut:** {download}`Download the runbook <JS2_Circuits-from-Datasheet_Runbook.md>`, give it to
your AI coding agent, and tell it to follow the file.

Build a board from a data sheet by prompting an agent that drives `jitx-circuit-builder`. The agent
reads the Microchip KSZ9031RNX gigabit Ethernet PHY data sheet and builds its application circuit
behind typed ports, with the strap configuration as an argument and the 1.2 V core made by the
PHY's own LDO controller. It then composes the circuit with a 3.3 V buck and an RJ45 jack. Each
runbook step is a request, phrased the way you would ask an agent for the work; the data sheet,
Microchip's ANLAN206 application note and the skill supply the engineering. What you learn is the
parametric circuit pattern: a circuit written once with its configuration as arguments, so one
circuit serves each configuration you need and a change of configuration is an argument and a
rebuild.

It is proven when the strap resistors match the data sheet's strap table, every supply pin has its
own decoupling capacitor, the design builds, and every passive comes from the example catalogue.
SI constraints and routing structures are left for JumpStart 4. The reference solution's code
states where the design falls short, among them that the LDO's MOSFET misses the data sheet's
gate-voltage window across its threshold spread, its turn-off at the core's lightest loads is
unverified, and the core powers down after 3.3 V rather than before it.

JS2 does not build on JS1: every component comes from the `jitxexamples` package, and the agent
models none.

## Before you start

- Finish [JS0](../js0-setup/).
- Start a new agent session. A skills install only takes effect in a session started after it.
- Download the runbook, linked below. The agent reads the data sheet from Microchip's site.
- Allow about 20 minutes of agent time, plus the time you spend at the three decisions below.
- To compare this run with your current flow afterward, note now roughly how long building an
  application circuit from a data sheet takes your team, what tends to go wrong, and how long a
  change of strap configuration takes to carry through the schematic. During the run, time it, time
  gate 3 from your request to the agent's report, and note anything the checks caught.

## What the agent asks of you

Three `[HUMAN]` gates stop for you:

1. **Choose the strap configuration.** The agent shows you its strap table beside the data sheet's
   and proposes a configuration. You confirm it or change the PHY address, mode, clock output or
   LED mode.
2. **Choose the input voltage.** The agent proposes an input and sizes the buck, with the
   regulator's checks. You choose.
3. **Change the configuration.** Ask for a different PHY address and mode (the runbook suggests
   one) and the agent rebuilds and tells you which strap resistors moved.

## After the run

You can now build a parametric circuit from a data sheet and change its configuration by argument.
Set gate 3's time against the same strap change in your current flow, up to the schematic; that
comparison counts for more than the whole run's time against your note, since a first run includes
learning. Set anything the checks caught beside what tends to go wrong in your flow. Then think
about which circuits your team rebuilds from board to board, and how you would share them: a
parametric circuit can go into a library, versioned and distributed across your company. Build one
of those this way and time it against the same note: that second run is the fairer measure.

## Files

- [The runbook](JS2_Circuits-from-Datasheet_Runbook.md), to read here;
  {download}`download it <JS2_Circuits-from-Datasheet_Runbook.md>` to give to your agent.
- The reference solution, module
  [`jitxexamples.jumpstart_kits.js2_circuits`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js2_circuits)
  in the `jitxexamples` package (`pip install jitxexamples`).
