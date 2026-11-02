"""Parse every docstring under ``src/jitxexamples`` the way the docs build does.

``docs/Makefile`` runs ``sphinx-apidoc`` over ``src/jitxexamples`` and feeds the
result to Sphinx, and ``pyproject.toml`` ships ``jumpstart-kits/`` in the sdist
so docs.jitx.com can extract it. Both surfaces render these docstrings as
reStructuredText, and neither fails the build on a malformed one — Sphinx is not
run with ``-W``, ruff selects no docstring rules, and there is no ``doc8`` or
``rstcheck``. So a broken docstring degrades silently into wrong HTML.

This test is that gate. It reads docstrings with ``ast`` rather than importing
anything, so it needs no JITX runtime and no parts database.

Two details make the difference between a useful gate and a noisy one:

* **napoleon runs first.** Sphinx rewrites Google- and NumPy-style sections
  before docutils ever sees them. Skipping that step reports Google-style
  parameter blocks as broken when they are fine.
* **Role and directive resolution messages are dropped.** Sphinx resolves its
  own domain roles (``:class:``, ``:meth:``, ...); bare docutils cannot, and
  would flag every one. Filtering the messages beats maintaining a list of roles
  to register, which would rot the first time someone uses a new one.

What is left is the structural layer docutils and Sphinx agree on: indentation,
blank lines, list and literal-block boundaries, title underlines.
"""

from __future__ import annotations

import ast
import io
import re
from pathlib import Path

from docutils.core import publish_doctree
from jitx.test import TestCase
from sphinx.ext.napoleon.docstring import GoogleDocstring, NumpyDocstring

SRC = Path(__file__).resolve().parents[1] / "src" / "jitxexamples"

#: Messages that only mean "this role/directive belongs to Sphinx, not docutils".
_RESOLUTION_NOISE = re.compile(
    r"Unknown interpreted text role"
    r"|No role entry for"
    r"|Unknown directive type"
    r"|No directive entry for"
)

_DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _rst_messages(docstring: str) -> list[str]:
    """Return docutils messages at WARNING or above, minus resolution noise."""
    # No config: napoleon then builds its own defaults, which is what Sphinx
    # uses here -- docs/source/conf.py sets no napoleon_* option.
    text = str(NumpyDocstring(str(GoogleDocstring(docstring))))
    stream = io.StringIO()
    publish_doctree(
        text,
        settings_overrides={
            "report_level": 2,  # WARNING and above
            "halt_level": 5,  # never raise; collect everything
            "warning_stream": stream,
            "_disable_config": True,
        },
    )
    return [
        line
        for line in stream.getvalue().splitlines()
        if line.startswith("<string>") and not _RESOLUTION_NOISE.search(line)
    ]


class TestDocstringRST(TestCase):
    def test_docstrings_are_well_formed_rst(self):
        failures: list[str] = []
        scanned = 0
        for path in sorted(SRC.rglob("*.py")):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, _DOCSTRING_OWNERS):
                    continue
                docstring = ast.get_docstring(node)
                if not docstring:
                    continue
                scanned += 1
                messages = _rst_messages(docstring)
                if not messages:
                    continue
                owner = getattr(node, "name", "<module>")
                rel = path.relative_to(SRC.parents[1])
                # docutils line numbers are relative to the docstring, so give
                # the reader both: where the docstring starts, and where in it.
                failures.append(
                    f"{rel}:{getattr(node, 'lineno', 1)} ({owner}) "
                    f"-- lines below are docstring-relative:\n    "
                    + "\n    ".join(messages)
                )
        self.assertGreater(scanned, 0, f"no docstrings found under {SRC}")
        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {scanned} docstrings are malformed reST:\n\n"
            + "\n\n".join(failures),
        )
