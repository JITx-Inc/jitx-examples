"""Pytest configuration for component tests.

This module provides mock fixtures for parts database queries, allowing tests
to run without requiring API access to the JITX parts database.

The mock returns real-format JSON data that was captured from actual API responses,
with values modified to match query parameters.

Note: The coverage configuration in pyproject.toml includes settings to
ignore the "dummy" filename that jitxlib uses when dynamically compiling
code from parts database queries.
"""

import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

# Load template JSON files (captured from real API responses)
_TEMPLATE_DIR = Path(__file__).parent.parent / "captured_json"

_TEMPLATES: dict[str, dict] = {}


def _load_templates():
    """Load JSON templates from captured_json directory."""
    global _TEMPLATES
    if _TEMPLATES:
        return

    for category in ["resistor", "capacitor", "inductor"]:
        template_file = _TEMPLATE_DIR / f"{category}_minimal.json"
        if template_file.exists():
            with open(template_file) as f:
                _TEMPLATES[category] = json.load(f)


def _make_dummy_json(category: str, **kwargs) -> dict:
    """Create dummy JSON for a part based on the template.

    Args:
        category: The part category (resistor, capacitor, inductor)
        **kwargs: Values to override in the template (e.g., resistance=1000.0)

    Returns:
        A dict containing valid part JSON
    """
    _load_templates()

    if category not in _TEMPLATES:
        # Fall back to resistor if unknown category
        category = "resistor"

    # Deep copy the template
    result = copy.deepcopy(_TEMPLATES[category])

    # Update values based on kwargs
    if category == "resistor" and "resistance" in kwargs:
        resistance = kwargs["resistance"]
        # Handle 0-ohm resistors (jumpers) - use a small non-zero value to avoid unit issues
        if resistance == 0 or resistance == 0.0:
            resistance = 0.001  # 1 milliohm, effectively 0 ohm
        result["resistance"] = resistance
        result["component"]["emodel"]["value"]["resistance"] = resistance

    elif category == "capacitor" and "capacitance" in kwargs:
        result["capacitance"] = kwargs["capacitance"]
        result["component"]["emodel"]["value"]["capacitance"] = kwargs["capacitance"]

    elif category == "inductor" and "inductance" in kwargs:
        result["inductance"] = kwargs["inductance"]
        result["component"]["emodel"]["value"]["inductance"] = kwargs["inductance"]

    # Update case if specified
    if "case" in kwargs:
        case = kwargs["case"]
        if isinstance(case, list):
            case = case[0]
        result["case"] = case

    return result


def mock_dbquery(args, limit=1000, skip_cache=False):
    """Mock dbquery that returns dummy parts based on the category."""
    category = args.get("category", "resistor")

    kwargs = {}
    if "resistance" in args:
        kwargs["resistance"] = args["resistance"]
    if "capacitance" in args:
        kwargs["capacitance"] = args["capacitance"]
    if "inductance" in args:
        kwargs["inductance"] = args["inductance"]
    if "case" in args:
        kwargs["case"] = args["case"]

    return [_make_dummy_json(category, **kwargs)]


@pytest.fixture(autouse=True)
def mock_parts_db(monkeypatch):
    """Automatically mock parts database queries for all tests.

    We patch dbquery in query_api module because that's where it's imported
    and used. Patching at commands.dbquery doesn't work because query_api
    imports dbquery directly into its namespace at module load time.

    Sets JITX_MOCK_PARTS_DB=1 environment variable so tests can check if
    the mock is active and skip tests that require the real database.
    """
    monkeypatch.setenv("JITX_MOCK_PARTS_DB", "1")
    with patch("jitxlib.parts.query_api.dbquery", side_effect=mock_dbquery):
        yield
