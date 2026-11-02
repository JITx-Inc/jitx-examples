"""JS3 Part 1 verification designs: show which RP2040 pin choices the provider
accepts.

Each design wraps the shipping ``McuMuxingCircuit`` unchanged, places the three
parts and closes every bus line with a code ``Route`` from a chosen RP2040 GPIO
to the peripheral pin. A route between two pins the provider may join is kept;
a route between pins no offered mapping joins is dropped. These routes fix the
mapping, which is why they live here and never in ``main.py``.

- ``McuMuxingProof``: SPI1 on GPIO 8 (RX), 9 (CSn), 10 (SCK) and 11 (TX), I2C0
  on GPIO 0 (SDA) and 1 (SCL). Every pair is in Table 279 of the RP2040
  datasheet, so every route is kept.
- ``McuMuxingProofIllegal``: the same, with SDA and SCL swapped (SDA on GPIO 1,
  SCL on GPIO 0). Table 279 offers no I2C SDA on GPIO 1 and no SCL on GPIO 0,
  so the two I2C routes are dropped.

The parts sit on the top layer with the flash and the accelerometer to the left
of the RP2040, whose GPIO 0 to 11 pins line its left edge.
"""

from jitx.circuit import Circuit, Route
from jitx.design import Design
from jitx.net import Port

from jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup.board import (
    HDIBoard,
    HDISubstrate,
)

from .main import McuMuxingCircuit

# GPIO numbers, from Table 279 of the RP2040 datasheet.
SPI1_GPIO = {"cipo": 8, "cs": 9, "sck": 10, "copi": 11}  # F1: SPI1 RX, CSn, SCK, TX
I2C0_GPIO = {"sda": 0, "scl": 1}  # F3: I2C0 SDA, SCL
I2C0_SWAPPED = {"sda": 1, "scl": 0}  # not offered: GPIO 1 is SCL only, GPIO 0 SDA only


class McuMuxingProofCircuit(Circuit):
    """``McuMuxingCircuit`` placed and code-routed on the given GPIO numbers."""

    def __init__(self, spi_gpio: dict[str, int], i2c_gpio: dict[str, int]) -> None:
        self.dut = McuMuxingCircuit()
        dut = self.dut
        mcu = dut.mcu.mcu
        flash = dut.flash.flash
        acc = dut.accel.acc

        mcu.at(0.0, 0.0)
        flash.at(-10.0, -3.0)
        acc.at(-8.0, 3.0)

        flash_pins: dict[str, Port] = {
            "cipo": flash.DO,
            "cs": flash.CS_NOT,
            "sck": flash.CLK,
            "copi": flash.DI,
        }
        # LIS3DH pin 4 is SCL, pin 6 SDA (datasheet Table 2).
        acc_pins: dict[str, Port] = {"sda": acc.SDA_SDI, "scl": acc.SPC}
        self.routes = [
            Route(mcu.GPIO[spi_gpio[name]], pin, layer=0)
            for name, pin in flash_pins.items()
        ] + [
            Route(mcu.GPIO[i2c_gpio[name]], pin, layer=0)
            for name, pin in acc_pins.items()
        ]


class McuMuxingProof(Design):
    """SPI1 on GPIO 8 to 11, I2C0 on GPIO 0 and 1: every route kept."""

    board = HDIBoard()
    substrate = HDISubstrate()

    def __init__(self) -> None:
        self.circuit = McuMuxingProofCircuit(SPI1_GPIO, I2C0_GPIO)


class McuMuxingProofIllegal(Design):
    """SDA and SCL swapped: the two I2C routes dropped."""

    board = HDIBoard()
    substrate = HDISubstrate()

    def __init__(self) -> None:
        self.circuit = McuMuxingProofCircuit(SPI1_GPIO, I2C0_SWAPPED)
