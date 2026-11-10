"""JS3 Part 1: the RP2040 model's I2C, SPI and UART pin options match datasheet Table
279, the legal-choice counts the runbook quotes follow from them, and the proof
designs route offered and unoffered pins as their names say. Offline: no
runtime needed."""

import itertools

from jitx.inspect import extract
from jitx.net import Port, Provide
from jitx.test import TestCase
from jitxlib.parts.lock import LockMode, force_mode

from jitxexamples.components.mcus.raspberry_pi_RP2040 import RP2040
from jitxexamples.jumpstart_kits.js3_pin_assignment.mcu_muxing.main import (
    McuMuxingCircuit,
    McuMuxingDesign,
)
from jitxexamples.jumpstart_kits.js3_pin_assignment.mcu_muxing.verify import (
    I2C0_GPIO,
    I2C0_SWAPPED,
    SPI1_GPIO,
)


def setUpModule() -> None:
    # Resolve parts with the lockfile off, as PartsTestDesign does, so a
    # test run never writes parts.lock.json at the repository root.
    force_mode(LockMode.OFF)


def tearDownModule() -> None:
    force_mode(None)


# RP2040 Datasheet (build-date 2025-02-20), Table 279: GPIO numbers per function,
# F1 (SPI) and F3 (I2C) columns, transcribed by hand.
TABLE_279: dict[str, list[int]] = {
    "I2C0_SDA": [0, 4, 8, 12, 16, 20, 24, 28],
    "I2C0_SCL": [1, 5, 9, 13, 17, 21, 25, 29],
    "I2C1_SDA": [2, 6, 10, 14, 18, 22, 26],
    "I2C1_SCL": [3, 7, 11, 15, 19, 23, 27],
    "SPI0_RX": [0, 4, 16, 20],
    "SPI0_CSn": [1, 5, 17, 21],
    "SPI0_SCK": [2, 6, 18, 22],
    "SPI0_TX": [3, 7, 19, 23],
    "SPI1_RX": [8, 12, 24, 28],
    "SPI1_CSn": [9, 13, 25, 29],
    "SPI1_SCK": [10, 14, 26],
    "SPI1_TX": [11, 15, 27],
}
# The F2 (UART) column. The kit does not use a UART; the model's lists were
# corrected with the others, so they are held to the table too.
TABLE_279_UART: dict[str, list[int]] = {
    "UART0_TX": [0, 12, 16, 28],
    "UART0_RX": [1, 13, 17, 29],
    "UART0_CTS": [2, 14, 18],
    "UART0_RTS": [3, 15, 19],
    "UART1_TX": [4, 8, 20, 24],
    "UART1_RX": [5, 9, 21, 25],
    "UART1_CTS": [6, 10, 22, 26],
    "UART1_RTS": [7, 11, 23, 27],
}


def _model_options(
    rp: RP2040, table: dict[str, list[int]] = TABLE_279
) -> dict[str, list[int]]:
    """GPIO numbers each single-pin function provide named in ``table`` offers,
    read from the model."""
    gpio_index = {id(port): i for i, port in enumerate(rp.mcu.GPIO)}
    out: dict[str, list[int]] = {}
    bundle_types = {name: getattr(RP2040, name) for name in table}
    for provide in extract(rp, Provide):
        names = [n for n, t in bundle_types.items() if isinstance(provide.bundle, t)]
        if not names:
            continue
        (name,) = names
        pins: list[int] = []
        for option in provide.options:
            ((_, target),) = option
            assert isinstance(target, Port)
            pins.append(gpio_index[id(target)])
        out[name] = sorted(pins)
    return out


def _rp2040() -> RP2040:
    circuit = McuMuxingDesign().circuit
    assert isinstance(circuit, McuMuxingCircuit)
    return circuit.mcu


def _bus_options(fn: dict[str, list[int]], names: list[str]) -> list[tuple[int, ...]]:
    return list(itertools.product(*(fn[n] for n in names)))


class TestJS3McuMuxing(TestCase):
    def test_model_pin_options_match_table_279(self) -> None:
        self.assertEqual(_model_options(_rp2040()), TABLE_279)

    def test_model_uart_options_match_table_279(self) -> None:
        self.assertEqual(_model_options(_rp2040(), TABLE_279_UART), TABLE_279_UART)

    def test_legal_choice_counts(self) -> None:
        fn = _model_options(_rp2040())
        i2c = _bus_options(fn, ["I2C0_SDA", "I2C0_SCL"]) + _bus_options(
            fn, ["I2C1_SDA", "I2C1_SCL"]
        )
        spi = _bus_options(
            fn, ["SPI0_RX", "SPI0_CSn", "SPI0_SCK", "SPI0_TX"]
        ) + _bus_options(fn, ["SPI1_RX", "SPI1_CSn", "SPI1_SCK", "SPI1_TX"])
        joint = sum(1 for a in i2c for b in spi if not set(a) & set(b))
        self.assertEqual((len(i2c), len(spi), joint), (113, 400, 34000))

    def test_proof_pins_are_offered_and_the_swap_is_not(self) -> None:
        t = TABLE_279
        self.assertIn(SPI1_GPIO["cipo"], t["SPI1_RX"])
        self.assertIn(SPI1_GPIO["cs"], t["SPI1_CSn"])
        self.assertIn(SPI1_GPIO["sck"], t["SPI1_SCK"])
        self.assertIn(SPI1_GPIO["copi"], t["SPI1_TX"])
        self.assertIn(I2C0_GPIO["sda"], t["I2C0_SDA"])
        self.assertIn(I2C0_GPIO["scl"], t["I2C0_SCL"])
        for sda_list, scl_list in (
            (t["I2C0_SDA"], t["I2C0_SCL"]),
            (t["I2C1_SDA"], t["I2C1_SCL"]),
        ):
            self.assertNotIn(I2C0_SWAPPED["sda"], sda_list)
            self.assertNotIn(I2C0_SWAPPED["scl"], scl_list)
