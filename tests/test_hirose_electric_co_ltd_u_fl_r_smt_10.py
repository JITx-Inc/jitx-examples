from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, InductorQuery, ResistorQuery

from jitxexamples.components.connectors.hirose_electric_co_ltd_U_FL_R_SMT_10 import (
    Device as U_FL_R_SMT_10Device,
)


class U_FL_R_SMT_10Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])
    _inductor_defaults = InductorQuery()

    @inline
    class circuit(Circuit):
        rf_connector = U_FL_R_SMT_10Device()


class TestUFLRSMT10(TestCase):
    def test_u_fl_r_smt_10(self):
        design = U_FL_R_SMT_10Design()
        self.assertIsInstance(design.circuit.rf_connector, U_FL_R_SMT_10Device)  # type: ignore
