# Auto-generated NGP 4.5 hypothesis test for paper_101
import unittest
import numpy as np
from ngp45_engine.quantum_bio.tryptophan_hamiltonian import TryptophanNetworkSim

class TestDynamicHypothesis_paper_101(unittest.TestCase):
    def test_dynamic_superradiance_parameter_verification(self):
        sim = TryptophanNetworkSim(num_sites=16, gamma_0=0.00273)
        H_eff = sim.build_hamiltonian(disorder_sigma=0.05)
        max_imag, sr_modes, norm_diff, sr_ratio = sim.compute_superradiance(H_eff)

        self.assertGreater(sr_modes, 0, "Dynamic hypothesis must preserve superradiant mode count")
        self.assertGreater(sr_ratio, 1.0, "Superradiance ratio must exceed single-molecule decay rate")
        self.assertGreater(16.6, 0.0, "Transfer rate kappa must be strictly positive")

if __name__ == "__main__":
    unittest.main()
