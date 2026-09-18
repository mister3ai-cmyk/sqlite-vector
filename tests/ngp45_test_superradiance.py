import time
import tracemalloc
import unittest
import numpy as np

from ngp45_engine.quantum_bio.tryptophan_hamiltonian import TryptophanNetworkSim


class TestTryptophanSuperradiance(unittest.TestCase):
    def setUp(self):
        self.sim = TryptophanNetworkSim(num_sites=16, gamma_0=0.00273)

    def test_non_hermitian_properties(self):
        """H_eff must be non-Hermitian: ||H - H†|| > 0."""
        H_eff = self.sim.build_hamiltonian(disorder_sigma=0.0)
        _, _, norm_diff, sr_ratio = self.sim.compute_superradiance(H_eff)
        print(f"\n[T3] Non-Hermiticity norm: {norm_diff:.6f}")
        self.assertGreater(norm_diff, 0.0)

    def test_superradiance_clean(self):
        """Clean network must exhibit ≥1 superradiant mode (SR ratio > 1)."""
        H_eff = self.sim.build_hamiltonian(disorder_sigma=0.0)
        max_imag, count, _, sr_ratio = self.sim.compute_superradiance(H_eff)
        print(f"\n[T3] Clean — SR ratio: {sr_ratio:.4f}  |  Superradiant modes: {count}")
        self.assertGreater(sr_ratio, 1.0, "SR ratio must exceed 1 for Dicke superradiance")
        self.assertGreater(count, 0)

    def test_superradiance_under_disorder(self):
        """Superradiance must persist under weak disorder (sigma=0.05 eV)."""
        H_eff = self.sim.build_hamiltonian(disorder_sigma=0.05)
        max_imag, count, _, sr_ratio = self.sim.compute_superradiance(H_eff)
        print(f"\n[T3] sigma=0.05 | SR ratio: {sr_ratio:.4f}  |  Superradiant modes: {count}")
        self.assertGreater(sr_ratio, 1.0)

    def test_disorder_stability_sweep_to_015(self):
        """SR ratio must remain > 1.0 for all sigma ∈ [0.0, 0.15] eV (boundary condition)."""
        results = self.sim.disorder_stability_sweep()
        print("\n[T3] Disorder stability sweep:")
        print(f"  {'sigma':>6}  {'SR ratio':>9}  {'SR modes':>9}  {'stable':>7}")
        print("  " + "-" * 40)
        for r in results:
            marker = "OK" if r["stable"] else "FAIL"
            print(f"  {r['sigma']:>6.2f}  {r['sr_ratio']:>9.4f}  "
                  f"{r['superradiant_count']:>9d}  {marker}")
        all_stable = all(r["stable"] for r in results)
        self.assertTrue(all_stable, "Superradiance collapsed under disorder — boundary condition violated")

    def test_benchmark_hamiltonian_and_superradiance(self):
        """Wall-time and peak-RSS for Hamiltonian build + superradiance computation."""
        tracemalloc.start()
        t0 = time.perf_counter()
        for _ in range(20):
            H_eff = self.sim.build_hamiltonian(disorder_sigma=0.05)
            self.sim.compute_superradiance(H_eff)
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"\n[T3-bench] 20x build+SR: {elapsed*1000:.2f}ms total  |  "
              f"Avg: {elapsed*1000/20:.2f}ms  |  Peak mem: {peak/1024:.1f}KB")
