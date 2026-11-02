"""JS3 Part 1 reference solution: an RP2040 drives an SPI data flash and an I2C
accelerometer, with every bus pin left to pin assignment.

Parts and sources:

- Raspberry Pi RP2040 (``jitxexamples.components.mcus.raspberry_pi_RP2040``).
  Its I2C and SPI pin options are the F1 (SPI) and F3 (I2C) columns of Table
  279, "General Purpose Input/Output (GPIO) User Bank Functions", section
  2.19.2: Raspberry Pi Ltd, "RP2040 Datasheet", build-date 2025-02-20,
  build-version 3184e62-clean,
  https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf.
- Winbond W25Q128JV serial flash (``W25Q128JVSIQ``), on standard SPI: Winbond,
  "W25Q128JV 3V 128M-bit serial flash memory with dual/quad SPI", Revision J,
  April 25, 2024 (read from the copy LCSC serves for part C97521,
  https://datasheet.lcsc.com/datasheet/pdf/d009d960f1daec6149edaa35b7dae856.pdf?productCode=C97521).
  Section 3.3 pins; section 4.2: standard SPI writes on DI and reads on DO;
  sections 4.3 and 4.4: /WP and /HOLD are active low, so both are held at VCC.
  Its 100 nF decoupling capacitor follows Raspberry Pi Ltd, "Hardware design
  with RP2040", build-date 20/08/2026, build-version 0444806419d7, Figure 7
  (C5, 100 nF on the W25Q128JVS VCC pin),
  https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf.
- STMicroelectronics LIS3DH accelerometer (``LIS3DHTR``), on I2C:
  STMicroelectronics, "LIS3DH", datasheet DocID17530 Rev 2, December 2016 (read
  from the copy LCSC serves for part C15134,
  https://datasheet.lcsc.com/datasheet/pdf/fe5ca48c88184deb9f920ce8b9b86aeb.pdf?productCode=C15134).
  Section 4: "When using the I2C, CS must be tied high"; Figure 5: 10 kOhm
  pull-ups from SCL and SDA to Vdd_IO when I2C is used. SA0 (pin 7) is tied to
  Vdd_IO, which selects the I2C address 0011001b (section 6.1.1).

Legal pin choices: Table 279 gives 113 for one I2C bus (I2C0 8 x 8, I2C1 7 x
7), 400 for one SPI bus with chip select (SPI0 4 x 4 x 4 x 4, SPI1 4 x 4 x 3 x
3), and 34,000 for both at once with no GPIO shared.

Out of scope: power entry. ``3V3`` is a named net with no regulator.
"""

from jitx.circuit import Circuit
from jitx.common import Power
from jitx.design import Design
from jitx.net import Net
from jitx.units import F, ohm
from jitxlib.parts import Capacitor, Resistor
from jitxlib.protocols.serial import I2C, SPI

from jitxexamples.components.flash.winbond_W25Q128JVSIQ import W25Q128JVSIQ
from jitxexamples.components.mcus.raspberry_pi_RP2040 import RP2040
from jitxexamples.components.sensors.stmicroelectronics_LIS3DHTR import LIS3DHTR
from jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup.board import (
    HDIBoard,
    HDISubstrate,
)

FLASH_DECOUPLING = 100e-9 * F
"""Hardware design with RP2040, Figure 7: C5, 100 nF on the flash VCC pin."""
I2C_PULLUP = 10e3 * ohm
"""LIS3DH datasheet Figure 5: Rpu = 10 kOhm on SCL and SDA to Vdd_IO."""


class DataFlash(Circuit):
    """A W25Q128JV on standard SPI, /WP and /HOLD held inactive."""

    spi = SPI(cs=True)
    power = Power()

    def __init__(self) -> None:
        self.flash = W25Q128JVSIQ()
        flash = self.flash
        self.decoupling = Capacitor(capacitance=FLASH_DECOUPLING)
        assert self.spi.cs and self.spi.copi and self.spi.cipo
        self.CS = self.spi.cs + flash.CS_NOT
        self.SCK = self.spi.sck + flash.CLK
        self.COPI = self.spi.copi + flash.DI
        self.CIPO = self.spi.cipo + flash.DO
        self.VCC = (
            self.power.Vp + flash.VCC + flash.IO2 + flash.IO3 + self.decoupling.p1
        )
        self.GND = self.power.Vn + flash.GND + self.decoupling.p2


class McuMuxingCircuit(Circuit):
    """RP2040 with an SPI flash and an I2C accelerometer; the RP2040 chooses
    the pins."""

    power = Power()
    """3V3 supply for every part."""

    def __init__(self) -> None:
        self.mcu = RP2040()
        self.flash = DataFlash()
        self.accel = LIS3DHTR()

        self.gnd = Net(
            [
                self.power.Vn,
                self.mcu.power.Vn,
                self.flash.power.Vn,
                self.accel.power.Vn,
            ],
            name="GND",
        )
        self.v3v3 = Net(
            [
                self.power.Vp,
                self.mcu.power.Vp,
                self.flash.power.Vp,
                self.accel.power.Vp,
                self.accel.vio,
            ],
            name="3V3",
        )

        # The buses are pin-assigned: keep the required bundles local.
        spi = self.mcu.require(SPI(cs=True))
        i2c = self.mcu.require(I2C)
        assert spi.cs and spi.copi and spi.cipo
        flash_spi = self.flash.spi
        assert flash_spi.cs and flash_spi.copi and flash_spi.cipo
        self.FLASH_SCK = spi.sck + flash_spi.sck
        self.FLASH_COPI = spi.copi + flash_spi.copi
        self.FLASH_CIPO = spi.cipo + flash_spi.cipo
        self.FLASH_CS = spi.cs + flash_spi.cs

        # The LIS3DH in I2C mode: CS high, SA0 high, 10 kOhm pull-ups.
        accel_spi = self.accel.spi
        assert accel_spi.cs and accel_spi.cipo
        self.i2c_pullups = [Resistor(resistance=I2C_PULLUP) for _ in range(2)]
        self.I2C_SDA = i2c.sda + self.accel.i2c.sda + self.i2c_pullups[0].p1
        self.I2C_SCL = i2c.scl + self.accel.i2c.scl + self.i2c_pullups[1].p1
        for pin in (
            self.i2c_pullups[0].p2,
            self.i2c_pullups[1].p2,
            accel_spi.cs,
            accel_spi.cipo,
        ):
            self.v3v3 += pin


class McuMuxingDesign(Design):
    """The shipping design: no placement, no routes, so the RP2040 keeps every
    legal pin choice open for whoever routes the board."""

    board = HDIBoard()
    substrate = HDISubstrate()
    circuit = McuMuxingCircuit()
