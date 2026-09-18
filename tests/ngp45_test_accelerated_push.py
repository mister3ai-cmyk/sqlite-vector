import time
import tracemalloc
import unittest
import numpy as np

from ngp45_engine.graph.accelerated_push import AcceleratedLocalPush


class TestAcceleratedLocalPush(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        self.n = 50
        adj = (np.random.rand(self.n, self.n) < 0.15).astype(float)
        np.fill_diagonal(adj, 0)
        self.adj = adj + adj.T
        self.alp = AcceleratedLocalPush(self.adj, alpha=0.15, epsilon=1e-4)

    def test_accelerated_push_ops_reduction(self):
        """Accelerated batch push must perform fewer push ops than naive sequential."""
        p_acc, ops_acc = self.alp.compute_ppr(seed_node=0)
        p_naive, ops_naive = self.alp.compute_naive_ppr(seed_node=0)
        print(f"\n[T1] Naive ops: {ops_naive:5d}  |  Accelerated ops: {ops_acc:5d}  "
              f"|  Reduction: {(1 - ops_acc/ops_naive)*100:.1f}%")
        self.assertLess(ops_acc, ops_naive)

    def test_ppr_l1_error_within_tolerance(self):
        """L1 distance between accelerated and naive PPR vectors must be < 0.1."""
        p_acc, _ = self.alp.compute_ppr(seed_node=0)
        p_naive, _ = self.alp.compute_naive_ppr(seed_node=0)
        l1_err = np.sum(np.abs(p_acc - p_naive))
        print(f"\n[T1] L1 error vs naive PPR: {l1_err:.6f}  (tolerance: 0.1)")
        self.assertLess(l1_err, 0.1)

    def test_ppr_probability_distribution(self):
        """Output PPR vector must sum to 1.0 (normalized distribution)."""
        p_acc, _ = self.alp.compute_ppr(seed_node=0)
        self.assertAlmostEqual(float(np.sum(p_acc)), 1.0, places=4)

    def test_benchmark_time_and_memory(self):
        """Wall-time and peak-RSS benchmark for accelerated vs naive."""
        tracemalloc.start()

        t0 = time.perf_counter()
        for seed in range(10):
            self.alp.compute_ppr(seed_node=seed % self.n)
        t_acc = time.perf_counter() - t0
        _, peak_acc = tracemalloc.get_traced_memory()

        tracemalloc.clear_traces()
        t0 = time.perf_counter()
        for seed in range(10):
            self.alp.compute_naive_ppr(seed_node=seed % self.n)
        t_naive = time.perf_counter() - t0
        _, peak_naive = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\n[T1-bench] Accelerated: {t_acc*1000:.1f}ms / {peak_acc/1024:.1f}KB  |  "
              f"Naive: {t_naive*1000:.1f}ms / {peak_naive/1024:.1f}KB")
