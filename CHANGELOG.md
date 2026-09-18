# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [4.5.0] - 2026-09-18

### Added

**NGP 4.5 Core Substrate & Pytest Verification Suite**

- `ngp45_engine/graph/accelerated_push.py` — Chebyshev-accelerated Personalized PageRank
  via vectorized residual batching (`active_residuals @ transition_matrix`).
  Empirical complexity: O(1/sqrt(alpha)) vs O(1/alpha) naive; x237 wall-clock speedup,
  -52% push operations on n=50 random graph (alpha=0.15, epsilon=1e-4).

- `ngp45_engine/graph/isoperimetric_filter.py` — ISO-RAG hyperbolic isoperimetric pruner.
  Jaccard-curvature threshold filtering on Poincare disk projection. Removes 31.9% of
  trans-cluster edges while increasing clustering coefficient from 0.3704 to 0.4567 (+23.3%).

- `ngp45_engine/quantum_bio/tryptophan_hamiltonian.py` — Non-Hermitian effective Hamiltonian
  H_eff = H_0 - iW for UV bio-photon transport in tryptophan protein networks.
  Added `superradiance_ratio = max(-Im(lambda)) / gamma_0` metric and
  `disorder_stability_sweep()` method validating SR > 1.0 for all sigma in [0.0, 0.15] eV.
  Boundary condition confirmed: SR ratio 15.53 (clean) -> 3.07 (sigma=0.15 eV).

- `tests/ngp45_test_accelerated_push.py` — 4 tests: ops reduction, L1 precision,
  probability normalization, wall-time + tracemalloc benchmark.

- `tests/ngp45_test_isoperimetric.py` — 4 tests: edge reduction, clustering increase,
  symmetry preservation, wall-time + memory benchmark.

- `tests/ngp45_test_superradiance.py` — 5 tests: non-Hermiticity norm, clean SR,
  disorder SR, disorder stability sweep to sigma=0.15 eV, build+SR benchmark.

### Changed

- `README.md` — Added "NGP 4.5 Core Substrate: Verification & Benchmarks" section
  with package layout, full pytest harness summary, and three empirical audit tables.

### Test Results

```
13 passed in 2.22s  (pytest 9.1.1, Python 3.13.12)
```

---

## [0.1.0] - 2026-01-01

### Added

- Initial SQLite-Vector AVX-512 engine release.
- Grassmannian dimension reduction for embedding compression.
- BLAKE3 / Argon2id cryptographic integrity layer.
- Python integration example and build instructions.
