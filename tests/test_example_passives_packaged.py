"""The example passives CSV ships inside the ``jitxexamples`` wheel.

A project that installed ``jitxexamples`` reads it with
``importlib.resources.files("jitxexamples") / "parts" / "example-passives.csv"``
and copies it out as a starting approved-parts list. Under the editable install
the tests run against, that expression resolves to the source tree whether or
not the wheel carries the file, so the packaging checks build a wheel from this
repository with its own build backend (``pip wheel``, into a temporary
directory) and read the CSV out of the archive.

The same wheel must carry ``seiko_epson_TSX_3225.csv``, the catalog the
TSX-3225 crystal family reads with ``importlib.resources`` when it is built.
"""

import csv
import io
import math
import re
import subprocess
import sys
import tempfile
import zipfile
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import NamedTuple
from unittest import TestCase

ROOT = Path(__file__).resolve().parent.parent
WHEEL_PATH = "jitxexamples/parts/example-passives.csv"
TSX_CATALOG_PATH = "jitxexamples/components/crystals/seiko_epson_TSX_3225.csv"
HEADER_START = ["category", "mpn", "manufacturer"]
CATEGORIES = ("resistor", "capacitor", "inductor")


class Rating(NamedTuple):
    case: str
    max_power: float  # W
    rated_voltage_dc: float  # V, the maximum working voltage
    jumper_max_current: float | None  # A


# Yageo RC_L series datasheet (V.14), Tables 2 and 3, the standard-power row
# for each size: power rating, maximum working voltage, and the jumper rated
# current from the JUMPER CRITERIA column.
YAGEO_RC_L = {
    "0201": Rating("0201", 1 / 20, 25, 0.5),
    "0402": Rating("0402", 1 / 16, 50, 1.0),
    "0603": Rating("0603", 1 / 10, 75, 1.0),
    "0805": Rating("0805", 1 / 8, 150, 2.0),
    "1206": Rating("1206", 1 / 4, 200, 2.0),
}

# Panasonic ERA A type datasheet, Ratings table, ERA2A (0402): power rating
# at 85 C and limiting element voltage. The series has no jumper.
PANASONIC_ERA = {"ERA-2AEB": Rating("0402", 0.063, 50, None)}


def _resource() -> Traversable:
    return files("jitxexamples") / "parts" / "example-passives.csv"


def _build_wheel(out_dir: Path) -> Path:
    """Build this repository's wheel into ``out_dir`` and return its path."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--quiet",
            "--wheel-dir",
            str(out_dir),
            str(ROOT),
        ],
        check=True,
    )
    (wheel,) = out_dir.glob("jitxexamples-*.whl")
    return wheel


class TestExamplePassivesPackaged(TestCase):
    wheel_names: list[str]
    rows: list[dict[str, str]]
    tsx_catalog: bytes | None

    @classmethod
    def setUpClass(cls) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(_build_wheel(Path(tmp))) as wheel:
                cls.wheel_names = wheel.namelist()
                text = (
                    wheel.read(WHEEL_PATH).decode("utf-8")
                    if WHEEL_PATH in cls.wheel_names
                    else ""
                )
                cls.tsx_catalog = (
                    wheel.read(TSX_CATALOG_PATH)
                    if TSX_CATALOG_PATH in cls.wheel_names
                    else None
                )
        cls.rows = list(csv.DictReader(io.StringIO(text)))

    def test_resource_resolves(self) -> None:
        self.assertTrue(_resource().is_file())

    def test_wheel_carries_the_csv(self) -> None:
        listed = [n for n in self.wheel_names if n.startswith("jitxexamples/parts/")]
        self.assertTrue(
            WHEEL_PATH in self.wheel_names, f"wheel jitxexamples/parts/: {listed}"
        )

    def test_wheel_carries_the_tsx_3225_catalog(self) -> None:
        listed = [
            n
            for n in self.wheel_names
            if n.startswith("jitxexamples/components/crystals/")
        ]
        self.assertIsNotNone(
            self.tsx_catalog, f"wheel jitxexamples/components/crystals/: {listed}"
        )
        self.assertEqual(
            self.tsx_catalog, (ROOT / "src" / TSX_CATALOG_PATH).read_bytes()
        )

    def test_header_and_categories(self) -> None:
        self.assertTrue(self.rows, f"{WHEEL_PATH} is missing or empty in the wheel")
        self.assertEqual(list(self.rows[0])[: len(HEADER_START)], HEADER_START)
        found = {row["category"] for row in self.rows}
        for category in CATEGORIES:
            self.assertIn(category, found)

    def test_every_resistor_has_a_power_rating(self) -> None:
        # A jumper is rated by the current it carries, not by power.
        resistors = [
            row
            for row in self.rows
            if row["category"] == "resistor" and row["type"] != "jumper"
        ]
        self.assertTrue(resistors)
        for row in resistors:
            with self.subTest(mpn=row["mpn"]):
                # A bare number in max_power is read as watts.
                self.assertGreater(float(row["max_power"] or "nan"), 0.0)

    def test_every_jumper_has_a_current_rating(self) -> None:
        jumpers = [
            row
            for row in self.rows
            if row["category"] == "resistor" and row["type"] == "jumper"
        ]
        self.assertTrue(jumpers)
        for row in jumpers:
            with self.subTest(mpn=row["mpn"]):
                # A bare number in max_current is read as amperes.
                self.assertGreater(float(row["max_current"] or "nan"), 0.0)
                self.assertEqual(row["max_power"], "")

    def test_every_inductor_has_a_current_rating(self) -> None:
        inductors = [row for row in self.rows if row["category"] == "inductor"]
        self.assertTrue(inductors)
        for row in inductors:
            with self.subTest(mpn=row["mpn"]):
                # A bare number in max_current is read as amperes.
                self.assertGreater(float(row["max_current"] or "nan"), 0.0)

    def test_resistor_ratings_match_the_datasheet_tables(self) -> None:
        resistors = [row for row in self.rows if row["category"] == "resistor"]
        self.assertTrue(resistors)
        for row in resistors:
            with self.subTest(mpn=row["mpn"]):
                yageo = re.match(r"RC(\d{4})", row["mpn"])
                if row["manufacturer"] == "Yageo" and yageo:
                    rating = YAGEO_RC_L.get(yageo.group(1))
                else:
                    rating = PANASONIC_ERA.get(row["mpn"][:8])
                    self.assertEqual(row["manufacturer"], "Panasonic")
                assert rating is not None, "no datasheet table for this series"
                self.assertEqual(row["case"], rating.case)
                if row["type"] == "jumper":
                    assert rating.jumper_max_current is not None
                    self.assertTrue(
                        math.isclose(
                            float(row["max_current"]), rating.jumper_max_current
                        )
                    )
                    continue
                self.assertTrue(
                    math.isclose(float(row["max_power"] or "nan"), rating.max_power),
                    f"max_power {row['max_power']}, table {rating.max_power}",
                )
                self.assertTrue(
                    math.isclose(
                        float(row["rated_voltage_dc"] or "nan"),
                        rating.rated_voltage_dc,
                    ),
                    f"rated_voltage_dc {row['rated_voltage_dc']}, "
                    f"table {rating.rated_voltage_dc}",
                )

    def test_larger_yageo_cases_mirror_rc0201(self) -> None:
        def resistances(size: str) -> list[str]:
            return [
                row["resistance"]
                for row in self.rows
                if row["category"] == "resistor" and row["mpn"].startswith(f"RC{size}")
            ]

        rc0201 = resistances("0201")
        self.assertEqual(len(rc0201), 122)
        for size in ("0603", "0805", "1206"):
            with self.subTest(size=size):
                self.assertEqual(resistances(size), rc0201)
