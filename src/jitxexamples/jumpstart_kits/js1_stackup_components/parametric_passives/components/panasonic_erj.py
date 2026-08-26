"""Panasonic ERJ general-purpose chip resistor family (parameterized).

Models Panasonic's general-purpose +/-5% thick-film chip resistor series (the
"ERJ-G" parts, datasheet AOA0000C301) as a single parameterized
:class:`jitx.Component`. Choose a case size and resistance and the component
builds the matching land pattern, resistor symbol, and Panasonic part number
with no parts-database or online lookup. It is a drop-in alternative to
:class:`jitxlib.parts.Resistor` and provides a matching :meth:`PanasonicERJ.insert`.

This datasheet covers the +/-5% (tolerance code J) general-purpose series only;
Panasonic's +/-1% / +/-0.5% precision parts are a separate series/datasheet.

Case sizes: 01005, 0201, 0402, 0603, 0805, 1206, 1210, 1812, 2010, 2512. Per the
datasheet, the larger sizes (1206/1210/1812/2010/2512) are marked
"not recommended for new design".

Datasheet (doc AOA0000C301); all dimensions below are transcribed from its
Dimensions table:
https://industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/AOA0000C301.pdf

Land-pattern construction, two-pin ``.insert()``, and the E-series check are
shared with the other chip-resistor families via :mod:`.chip_smt`.
"""

import math
from typing import Self

import jitx
from jitx.net import Net, Port
from jitx.units import PlainQuantity, ohm
from jitxlib.symbols.resistor import ResistorSymbol

from .chip_smt import (
    ChipDims,
    check_eseries as _check_eseries,
    chip_smt_landpattern,
    datasheet_dim as _t,
    compact_value,
    insert_two_pin,
    round_sig,
)

DATASHEET_URL = (
    "https://industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/AOA0000C301.pdf"
)


# Imperial case size -> Panasonic part-number size code (ordering positions 4-6).
# The size code is NOT the imperial size. 1GJ (0201) is the AEC-Q200 grade-1 part
# used for new designs; 1GN is the legacy general variant. Sizes flagged NRFND are
# "not recommended for new design" per the datasheet.
SIZE_CODE: dict[str, str] = {
    "01005": "XGN",
    "0201": "1GJ",
    "0402": "2GE",
    "0603": "3GE",
    "0805": "6GE",
    "1206": "8GE",  # NRFND
    "1210": "14",  # NRFND
    "1812": "12",  # NRFND
    "2010": "12Z",  # NRFND
    "2512": "1T",  # NRFND
}

# Size codes printed WITHOUT the value-marking letter "Y" in the part number.
_NO_MARKING = ("XGN", "1GN", "1GJ", "2GE")

# Dimensions (mm) from the datasheet Dimensions table, mapped to ChipDims
# (length L, width W, height/thickness T, lead = bottom electrode "b").
# _t(typ, +/-) is symmetric; _t(typ, plus, minus) is asymmetric.
ERJ_DIMENSIONS: dict[str, ChipDims] = {
    "01005": ChipDims(_t(0.40, 0.02), _t(0.20, 0.02), _t(0.13, 0.02), _t(0.10, 0.03)),
    "0201": ChipDims(_t(0.60, 0.03), _t(0.30, 0.03), _t(0.23, 0.03), _t(0.15, 0.05)),
    "0402": ChipDims(_t(1.00, 0.05), _t(0.50, 0.05), _t(0.35, 0.05), _t(0.25, 0.05)),
    "0603": ChipDims(
        _t(1.60, 0.15), _t(0.80, 0.15, 0.05), _t(0.45, 0.10), _t(0.30, 0.15)
    ),
    "0805": ChipDims(_t(2.00, 0.20), _t(1.25, 0.10), _t(0.60, 0.10), _t(0.40, 0.20)),
    "1206": ChipDims(
        _t(3.20, 0.05, 0.20), _t(1.60, 0.05, 0.15), _t(0.60, 0.10), _t(0.50, 0.20)
    ),
    "1210": ChipDims(_t(3.20, 0.20), _t(2.50, 0.20), _t(0.60, 0.10), _t(0.50, 0.20)),
    "1812": ChipDims(_t(4.50, 0.20), _t(3.20, 0.20), _t(0.60, 0.10), _t(0.50, 0.20)),
    "2010": ChipDims(_t(5.00, 0.20), _t(2.50, 0.20), _t(0.60, 0.10), _t(0.60, 0.20)),
    "2512": ChipDims(_t(6.40, 0.20), _t(3.20, 0.20), _t(0.60, 0.10), _t(0.60, 0.20)),
}

# Rated power (W at 70 C) per size (datasheet Ratings table).
POWER_RATING: dict[str, float] = {
    "01005": 0.031,
    "0201": 0.05,
    "0402": 0.1,
    "0603": 0.1,
    "0805": 0.125,
    "1206": 0.25,
    "1210": 0.5,
    "1812": 0.75,
    "2010": 0.75,
    "2512": 1.0,
}

# Limiting element (max working) voltage (V) per size.
MAX_VOLTAGE: dict[str, int] = {
    "01005": 15,
    "0201": 25,
    "0402": 50,
    "0603": 75,
    "0805": 150,
    "1206": 200,
    "1210": 200,
    "1812": 200,
    "2010": 200,
    "2512": 200,
}

# Maximum resistance (ohms) per size; the E24 range is 1 ohm up to this value.
RES_MAX: dict[str, float] = {
    "01005": 1e6,
    "0201": 10e6,
    "0402": 10e6,
    "0603": 10e6,
    "0805": 10e6,
    "1206": 10e6,
    "1210": 10e6,
    "1812": 10e6,
    "2010": 10e6,
    "2512": 1e6,
}

# Default packaging-field code per size (datasheet packaging table).
PACKAGING_DEFAULT: dict[str, str] = {
    "01005": "Y",
    "0201": "U",
    "0402": "X",
    "0603": "V",
    "0805": "V",
    "1206": "V",
    "1210": "U",
    "1812": "U",
    "2010": "U",
    "2512": "U",
}
PACKAGING_CODES = ("Y", "U", "C", "X", "V")

# This datasheet is the +/-5% (code J) general-purpose series only.
TOLERANCE_CODE: dict[float, str] = {0.05: "J"}


def format_value_code(ohms: float) -> str:
    """Encode a resistance as Panasonic's 3-character E24 value code.

    Two significant figures followed by a zero-count exponent; values below
    10 ohms use ``R`` as the decimal point.

    >>> format_value_code(1000)
    '102'
    >>> format_value_code(2200)
    '222'
    >>> format_value_code(4.7)
    '4R7'
    >>> format_value_code(1_000_000)
    '105'
    """
    if not 1 <= ohms <= 10e6:
        raise ValueError(f"resistance {ohms} ohms out of E24 range (1 to 10M)")
    ohms = round_sig(ohms, 2)  # E24 -> 2 significant figures; propagates carries
    if ohms < 10:
        whole = int(ohms)
        return f"{whole}R{round((ohms - whole) * 10)}"
    exponent = int(math.floor(math.log10(ohms))) - 1
    significant = round(ohms / (10**exponent))
    if significant >= 100:  # rounding carried into a new decade (e.g. 9.95e3)
        significant //= 10
        exponent += 1
    return f"{significant}{exponent}"


def _build_mpn(size: str, ohms: float, packaging: str) -> str:
    """Assemble the Panasonic ERJ part number (e.g. ``ERJ3GEYJ102V``).

    Tolerance is always ``J`` (+/-5%) for this general-purpose series.
    """
    code = SIZE_CODE[size]
    marking = "" if code in _NO_MARKING else "Y"
    return f"ERJ{code}{marking}J{format_value_code(ohms)}{packaging}"


class PanasonicERJ(jitx.Component):
    """A Panasonic ERJ general-purpose +/-5% chip resistor, from datasheet data.

    Args:
        resistance: Resistance in ohms (1 to the size's maximum, E24 values).
        size: Imperial case code, e.g. ``"0603"``. One of the supported sizes
            (01005 .. 2512).
        tolerance: Tolerance as a fraction. Only ``0.05`` (+/-5%, code J) is
            available in this general-purpose series.
        packaging: Packaging-field code (Y/U/C/X/V). ``None`` uses the size's
            datasheet default.
        check_eseries: If true, validate ``resistance`` against the E24 grid.
    """

    datasheet: str
    p1: Port
    p2: Port
    landpattern: jitx.Landpattern
    symbol: jitx.Symbol
    case: str
    tolerance: float
    power: float
    max_voltage: int

    def __init__(
        self,
        *,
        resistance: float,
        size: str = "0402",
        tolerance: float = 0.05,
        packaging: str | None = None,
        check_eseries: bool = False,
    ):
        if size not in SIZE_CODE:
            raise ValueError(
                f"Unknown Panasonic ERJ size {size!r}; supported sizes: "
                f"{sorted(SIZE_CODE)}"
            )
        if tolerance not in TOLERANCE_CODE:
            raise ValueError(
                f"tolerance {tolerance} not available in the ERJ-G general-purpose "
                f"series, which is +/-5% only ({sorted(TOLERANCE_CODE)} = J); "
                f"precision tolerances are a separate Panasonic datasheet"
            )
        res_max = RES_MAX[size]
        if not 1 <= resistance <= res_max:
            raise ValueError(
                f"resistance {resistance} ohms out of range for size {size} "
                f"(1 to {res_max:,.0f} ohms)"
            )
        if packaging is None:
            packaging = PACKAGING_DEFAULT[size]
        elif packaging not in PACKAGING_CODES:
            raise ValueError(
                f"packaging {packaging!r} invalid; choose one of {PACKAGING_CODES}"
            )
        if check_eseries:
            _check_eseries(resistance, tolerance)

        self.mpn = _build_mpn(size, resistance, packaging)
        self.manufacturer = "Panasonic"
        self.reference_designator_prefix = "R"
        self.datasheet = DATASHEET_URL
        self.value = compact_value(PlainQuantity(resistance, ohm))
        self.case = size
        self.tolerance = tolerance
        self.power = POWER_RATING[size]
        self.max_voltage = MAX_VOLTAGE[size]

        self.symbol = ResistorSymbol()
        self.landpattern = chip_smt_landpattern(size, ERJ_DIMENSIONS[size])

        # Two symmetric terminals; declaration order drives the default
        # port -> symbol-pin -> pad mapping (p1 -> p[1], p2 -> p[2]).
        self.p1 = Port()
        self.p2 = Port()

    def insert(
        self,
        pin_a: Port | Net,
        pin_b: Port | Net,
        *,
        short_trace: bool = False,
    ) -> Self:
        """Place this resistor between two pins/nets of the active circuit.

        Mirrors :meth:`jitxlib.parts.Resistor.insert`; see
        :func:`.chip_smt.insert_two_pin`.
        """
        return insert_two_pin(self, pin_a, pin_b, short_trace=short_trace)


Device: type[PanasonicERJ] = PanasonicERJ
