import os
import re
import sys
import unittest
from pathlib import Path
from typing import Dict


class DynamicTestRunner:
    """
    Hypothesis Runner & Test Generator for NGP 4.5 Auto-Research Harness.
    Extracts physical/numerical parameters from harvested documents,
    generates dynamic pytest verification scripts, and executes test suites.
    """

    def __init__(self, output_dir: str | None = None):
        if output_dir is None:
            # Cross-platform: tests/dynamic_research/ next to this file
            output_dir = str(Path(__file__).parent.parent.parent / "tests" / "dynamic_research")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        init_file = os.path.join(self.output_dir, "__init__.py")
        if not os.path.exists(init_file):
            Path(init_file).write_text("# Dynamic Research Tests Package\n", encoding="utf-8")

    def _parse_float(self, val_str: str) -> float:
        return float(val_str.rstrip("."))

    def extract_parameters(self, text: str) -> Dict[str, float]:
        params: Dict[str, float] = {}

        m = re.search(r'intercept\s*=?\s*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
        if m:
            params["dunedin_intercept"] = self._parse_float(m.group(1))

        m = re.search(r'kappa\s*=?\s*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
        if m:
            params["kappa"] = self._parse_float(m.group(1))

        m = re.search(r'sigma\s*=?\s*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
        if m:
            params["sigma"] = self._parse_float(m.group(1))

        m = re.search(r'gamma_0\s*=?\s*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
        if m:
            params["gamma_0"] = self._parse_float(m.group(1))

        return params

    def generate_test_file(self, doc_id: str, params: Dict[str, float]) -> str:
        clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", doc_id)
        filepath = os.path.join(self.output_dir, f"test_dynamic_{clean_id}.py")

        sigma_val = params.get("sigma", 0.05)
        gamma_val = params.get("gamma_0", 0.00273)
        kappa_val = params.get("kappa", 16.6)

        # Template is synchronized with actual TryptophanNetworkSim API:
        #   - constructor: num_sites=16
        #   - build:       build_hamiltonian(disorder_sigma=...)
        #   - returns:     (max_imag, superradiant_count, norm_diff, sr_ratio)
        test_code = f"""# Auto-generated NGP 4.5 hypothesis test for {doc_id}
import unittest
import numpy as np
from ngp45_engine.quantum_bio.tryptophan_hamiltonian import TryptophanNetworkSim

class TestDynamicHypothesis_{clean_id}(unittest.TestCase):
    def test_dynamic_superradiance_parameter_verification(self):
        sim = TryptophanNetworkSim(num_sites=16, gamma_0={gamma_val})
        H_eff = sim.build_hamiltonian(disorder_sigma={sigma_val})
        max_imag, sr_modes, norm_diff, sr_ratio = sim.compute_superradiance(H_eff)

        self.assertGreater(sr_modes, 0, "Dynamic hypothesis must preserve superradiant mode count")
        self.assertGreater(sr_ratio, 1.0, "Superradiance ratio must exceed single-molecule decay rate")
        self.assertGreater({kappa_val}, 0.0, "Transfer rate kappa must be strictly positive")

if __name__ == "__main__":
    unittest.main()
"""
        Path(filepath).write_text(test_code, encoding="utf-8")
        return filepath

    def run_generated_test(self, test_filepath: str) -> bool:
        dir_name = os.path.dirname(test_filepath)
        module_name = os.path.splitext(os.path.basename(test_filepath))[0]

        if dir_name not in sys.path:
            sys.path.insert(0, dir_name)

        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(module_name)
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, "w"))
        result = runner.run(suite)
        return result.wasSuccessful()
