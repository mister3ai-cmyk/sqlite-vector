import time
import tracemalloc
import unittest
import numpy as np

from ngp45_engine.graph.isoperimetric_filter import IsoperimetricPruner


class TestIsoperimetricPruning(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        self.n = 40
        adj = (np.random.rand(self.n, self.n) < 0.2).astype(float)
        np.fill_diagonal(adj, 0)
        self.adj = adj + adj.T
        self.pruner = IsoperimetricPruner(curvature_threshold=0.15)

    def test_pruning_reduces_edges(self):
        """Pruning must remove at least one edge from the original graph."""
        pruned = self.pruner.prune_graph(self.adj)
        orig_edges = np.sum(self.adj > 0) // 2
        pruned_edges = np.sum(pruned > 0) // 2
        print(f"\n[T2] Edges: {orig_edges} -> {pruned_edges} "
              f"({(1 - pruned_edges/orig_edges)*100:.1f}% pruned)")
        self.assertLess(pruned_edges, orig_edges)

    def test_pruning_increases_clustering(self):
        """After pruning, clustering coefficient must be strictly higher."""
        pruned = self.pruner.prune_graph(self.adj)
        cc_orig = IsoperimetricPruner.clustering_coefficient(self.adj)
        cc_pruned = IsoperimetricPruner.clustering_coefficient(pruned)
        print(f"\n[T2] Clustering: {cc_orig:.4f} -> {cc_pruned:.4f} "
              f"(delta={cc_pruned - cc_orig:+.4f})")
        self.assertGreater(cc_pruned, cc_orig)

    def test_symmetry_preserved(self):
        """Pruned graph must remain undirected (symmetric adjacency)."""
        pruned = self.pruner.prune_graph(self.adj)
        self.assertTrue(np.allclose(pruned, pruned.T))

    def test_benchmark_time_and_memory(self):
        """Wall-time and peak-RSS benchmark for graph pruning."""
        tracemalloc.start()
        t0 = time.perf_counter()
        self.pruner.prune_graph(self.adj)
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"\n[T2-bench] Prune time: {elapsed*1000:.2f}ms  |  Peak mem: {peak/1024:.1f}KB")
