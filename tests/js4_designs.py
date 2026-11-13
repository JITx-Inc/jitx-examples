"""JS4 test designs, shared by the JS4 test modules only.

They live apart from ``tests.parts`` so a failure importing the JS4 kit or its
substrate stops only the modules that use them.
"""

from functools import cache

from jitxexamples.jumpstart_kits.js4_fpga_lpddr4.base import JS4BaseDesign
from jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part4_routing import JS4RoutingDesign
from jitxexamples.substrates.reference_18layer import (
    Reference18Board,
    Reference18Substrate,
)
from tests.parts import PartsTestDesign


class JS4BaseTestDesign(PartsTestDesign, JS4BaseDesign):
    """The JS4 base design, resolving passives through the test parts chain,
    with no lockfile written. The board and substrate are restated so the
    sample design's do not shadow the reference ones."""

    board = Reference18Board()
    substrate = Reference18Substrate()


class JS4RoutingTestDesign(PartsTestDesign, JS4RoutingDesign):
    """Part 4's reference design, on the test parts chain."""

    board = Reference18Board()
    substrate = Reference18Substrate()


@cache
def js4_base_design() -> JS4BaseTestDesign:
    """One shared instantiation; call only inside a TestCase."""
    return JS4BaseTestDesign()


@cache
def js4_routing_design() -> JS4RoutingTestDesign:
    """One shared instantiation of Part 4's design; call only inside a
    TestCase."""
    return JS4RoutingTestDesign()
