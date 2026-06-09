# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Add jitx source to import path
import os
import sys
from pathlib import Path
from sphinx.ext import autodoc

os.environ["JITX_PASSIVE_INSTANTIATION"] = "1"
sys.path.insert(0, str(Path("..", "..", "src").resolve()))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "jitxexamples"
copyright = "2025, JITX Inc"  # noqa: A001
author = "JITX Inc"
version = "0.1"
release = "0.1.0dev1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

needs_sphinx = "8.1"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]
templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

# -- Don't show "Bases: object" in api docs ----------------------------------
# https://stackoverflow.com/questions/46279030/how-can-i-prevent-sphinx-from-listing-object-as-a-base-class


class MockedClassDocumenter(autodoc.ClassDocumenter):
    def add_line(self, line: str, source: str, *lineno: int) -> None:
        if line == "   Bases: :py:class:`object`":
            return
        super().add_line(line, source, *lineno)


autodoc.ClassDocumenter = MockedClassDocumenter
