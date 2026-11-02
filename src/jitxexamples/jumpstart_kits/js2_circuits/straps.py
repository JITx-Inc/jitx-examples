"""Strap-in configuration of the KSZ9031RNX.

Transcribed from Table 2-2 ("Strap-In Options - KSZ9031RNX") of data sheet
DS00002117K. Each strap-in function is latched from the level on its pin at
power-up or reset: a pull-up latches 1, a pull-down latches 0. The strap pins
have no internal pull (Table 2-1 types them I/O, and Table 6-6 lists internal
pull-ups only on MDC, MDIO and RESET_N), so every strap pin takes an external
resistor for every configuration.

======  ==========  ==================  =======================================
Pin     Pin name    Strap function      Value
======  ==========  ==================  =======================================
35      RX_CLK      PHYAD2              PHY address bit 2
15      LED2        PHYAD1              PHY address bit 1
17      LED1        PHYAD0              PHY address bit 0
27      RXD3        MODE3               ``Mode`` code bit 3
28      RXD2        MODE2               ``Mode`` code bit 2
31      RXD1        MODE1               ``Mode`` code bit 1
32      RXD0        MODE0               ``Mode`` code bit 0
33      RX_DV       CLK125_EN           1 enables the 125 MHz CLK125_NDO output
41      CLK125_NDO  LED_MODE            1 is single-LED, 0 tri-color dual-LED
======  ==========  ==================  =======================================
"""

from dataclasses import dataclass
from enum import Enum


class Strap(Enum):
    """A strap-in function of Table 2-2, valued by the pin number carrying it."""

    PHYAD2 = 35
    PHYAD1 = 15
    PHYAD0 = 17
    MODE3 = 27
    MODE2 = 28
    MODE1 = 31
    MODE0 = 32
    CLK125_EN = 33
    LED_MODE = 41


class Mode(Enum):
    """The MODE[3:0] codes Table 2-2 defines, valued by the 4-bit code.

    The codes it marks "Reserved - not used" (0000 to 0011, 0101, 0110, 1000 to
    1011) have no member, so ``Mode(0b0101)`` raises ``ValueError``.
    """

    NAND_TREE = 0b0100
    CHIP_POWER_DOWN = 0b0111
    RGMII_1000_FULL = 0b1100
    """RGMII, advertise 1000BASE-T full-duplex only."""
    RGMII_1000_FULL_HALF = 0b1101
    """RGMII, advertise 1000BASE-T full- and half-duplex only."""
    RGMII_ALL_EXCEPT_1000_HALF = 0b1110
    """RGMII, advertise 10/100/1000 half- and full-duplex except 1000BASE-T
    half-duplex."""
    RGMII_ALL = 0b1111
    """RGMII, advertise 10/100/1000 half- and full-duplex."""


class LedMode(Enum):
    """LED_MODE, valued by the latched bit."""

    TRI_COLOR_DUAL = 0
    SINGLE = 1


@dataclass(frozen=True)
class StrapConfig:
    """The configuration the strap resistors latch.

    Args:
        phy_address: PHYAD[2:0], 0 to 7. Address bits [4:3] are always 00.
        mode: MODE[3:0].
        clk125_output: CLK125_EN, whether CLK125_NDO drives a 125 MHz clock.
        led_mode: LED_MODE.

    Raises:
        ValueError: ``phy_address`` is outside 0 to 7.
    """

    phy_address: int = 0
    mode: Mode = Mode.RGMII_ALL
    clk125_output: bool = False
    led_mode: LedMode = LedMode.SINGLE

    def __post_init__(self) -> None:
        if not 0 <= self.phy_address <= 7:
            raise ValueError(
                f"KSZ9031RNX PHY address {self.phy_address} is outside 0 to 7: "
                "PHYAD[2:0] sets three bits"
            )
        if not isinstance(self.mode, Mode):
            raise TypeError(f"mode must be a Mode, not {self.mode!r}")
        if not isinstance(self.led_mode, LedMode):
            raise TypeError(f"led_mode must be a LedMode, not {self.led_mode!r}")

    def level(self, strap: Strap) -> bool:
        """The level ``strap`` latches: True for a pull-up, False for a pull-down."""
        match strap:
            case Strap.PHYAD2:
                return bool(self.phy_address & 0b100)
            case Strap.PHYAD1:
                return bool(self.phy_address & 0b010)
            case Strap.PHYAD0:
                return bool(self.phy_address & 0b001)
            case Strap.MODE3:
                return bool(self.mode.value & 0b1000)
            case Strap.MODE2:
                return bool(self.mode.value & 0b0100)
            case Strap.MODE1:
                return bool(self.mode.value & 0b0010)
            case Strap.MODE0:
                return bool(self.mode.value & 0b0001)
            case Strap.CLK125_EN:
                return self.clk125_output
            case Strap.LED_MODE:
                return self.led_mode is LedMode.SINGLE


DEFAULT_STRAPS = StrapConfig()
"""PHY address 0, every RGMII mode advertised, CLK125_NDO off, single-LED mode."""
