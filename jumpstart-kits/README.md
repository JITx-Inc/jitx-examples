# JumpStart Kits — collateral

Customer-facing JumpStart Kit collateral. The JITX docs build will extract this tree into the
documentation site's **JumpStart Kits** section; see `JUMPSTART-KITS.md` in `JITx-Inc/jitx-doc`
for the authoring contract.

This page is contributor-facing and is **not** published — the docs build generates the section's
landing page itself.

## What belongs here

Learner-facing narrative and collateral only: runbooks, reference companions, supplied inputs, and
decks. Importable solution code lives under `src/jitxexamples/jumpstart_kits/` where the repo's
ruff, pyright, and pytest gates cover it.

Internal material stays in `internal/` at the repo root: requirement specs, program TODOs, and
deck-production tooling. That tree is excluded from the sdist and from the public mirror, so it
reaches no deployment surface. **Every `.md` placed here, by contrast, will be published to
docs.jitx.com and into the site-root `llms.txt`** once the docs build picks up this section — so
write everything here as public from the outset, and never link from here into `internal/` (the
link would 404 on the docs site).

## Structure

One directory per kit, named `js<N>-<slug>`; `<N>` sets the order on the site. Every directory needs
a `README.md`, whose first `# H1` becomes the page title and its label in the left nav. Don't write
a `{toctree}` or a manual list of a directory's own pages — the docs build generates both.

Directories holding two or more documents, or any binaries, keep their level. A directory that would
hold a single document is flattened into its parent, so the site has no page whose only content is a
link to one child.

## Linking collateral, and the one place Sphinx syntax is needed

A plain relative markdown link is all you need for a deck, a PDF, or a supplied input: the docs build
turns a link to a **non-document** file into a real download, served from
`_downloads/<sha256-of-its-bytes>/<name>`.

A link to a `.md` file is different, because `.md` is a *document* suffix — that link resolves to the
published **page**, not a download. So a runbook can be read on the site but not saved from it, which
is the wrong action for a file whose whole purpose is to be handed to an agent. Where a page needs to
offer the raw markdown, use Sphinx's `download` role:

```markdown
{download}`Download JS0_Setup_Runbook.md <JS0_Setup_Runbook.md>`
```

That publishes the file *and* leaves it a page. It is the only Sphinx syntax in this tree, and it has
two consequences to keep in mind:

- **It doesn't render on GitHub**, where it shows as literal `{download}` text. Accepted deliberately:
  GitHub already gives a "Download raw file" button on the blob page, so the role buys nothing there.
- **The docs build cannot see it.** Kit navigation order is derived from the *markdown* links in a page
  body, and a page whose body lists no children with markdown links gets a second, visible contents
  listing. So **add** a `download` role alongside the existing markdown link; never replace one with it.
