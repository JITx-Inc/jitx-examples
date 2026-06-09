from jitx.circuit import Circuit
from jitx.net import Port
from jitxlib.parts.query_api import Resistor
from jitxlib.protocols.serial import I2C
from ..fets_n_ch.BSS138 import BSS138


class LogicLevelShifter(Circuit):
    """
    Logic Level Shifter Module
    Uses a BSS138 N-channel MOSFET to shift logic levels bidirectionally
    """

    hv = Port()  # High voltage supply
    lv = Port()  # Low voltage supply
    # gnd = Port()       # Ground
    lv_signal = Port()  # Low voltage signal
    hv_signal = Port()  # High voltage signal

    # BSS138 N-channel MOSFET
    fet = BSS138()

    # Pull-up resistors
    lv_pullup = Resistor(
        # description="Low voltage pull-up resistor",
        resistance=10.0e3,  # 10kΩ
    ).insert(lv_signal, lv)

    hv_pullup = Resistor(
        # description="High voltage pull-up resistor",
        resistance=10.0e3,  # 10kΩ
    ).insert(hv_signal, hv)

    # Circuit connections
    nets = [
        # MOSFET connections
        fet.S + lv_signal,  # Source to low voltage signal
        fet.D + hv_signal,  # Drain to high voltage signal
        fet.G + lv,  # Gate to low voltage supply
        # Pull-up resistor connections
        # fet.G + gnd,
    ]


class I2CLevelShifter(Circuit):
    """
    I2C Level Shifter Module
    Uses two logic level shifters for SCL and SDA lines
    """

    # gnd = Port()  # Ground
    lv = Port()  # Low voltage supply
    hv = Port()  # High voltage supply

    # Create level shifter instances
    scl_shift = LogicLevelShifter()
    sda_shift = LogicLevelShifter()

    # I2C ports
    lv_i2c = I2C()  # Low voltage I2C
    hv_i2c = I2C()  # High voltage I2C

    # I2C signal connections
    nets = [
        # SCL connections
        lv_i2c.scl + scl_shift.lv_signal,  # Low voltage SCL
        hv_i2c.scl + scl_shift.hv_signal,  # High voltage SCL
        # SDA connections
        lv_i2c.sda + sda_shift.lv_signal,  # Low voltage SDA
        hv_i2c.sda + sda_shift.hv_signal,  # High voltage SDA
        # Power connections
        hv + scl_shift.hv + sda_shift.hv,  # High voltage supply
        lv + scl_shift.lv + sda_shift.lv,  # Low voltage supply
        # gnd + scl_shift.gnd + sda_shift.gnd,  # Ground
    ]


Device: type[I2CLevelShifter] = I2CLevelShifter
