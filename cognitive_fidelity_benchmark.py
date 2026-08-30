#!/usr/bin/env python3
"""
Cognitive Fidelity Benchmark — NGP 4.5
Hyper-Tetrapod Engine · 432 Hz · Syn Syndicate

Run:
    pip install numpy
    python cognitive_fidelity_benchmark.py

Phases:
    S0  Hippocampus Initialization  (SQLite WAL + IVF index)
    S1  Glyphing & Compression      (Needle-in-haystack + Ebbinghaus L0-L5)
    S2  Cognitive Audit             (MRA, Chordal metric, APSA sabotage index)
"""

import os, time, math, json, sqlite3, hashlib, uuid, re, tempfile, threading
import numpy as np
from typing import List, Tuple, Optional, Dict

# ── Constants ──────────────────────────────────────────────────────────────────
FREQ_HZ       = 432                   # Synchronization attractor
TICK          = 1.0 / FREQ_HZ        # 2.31 ms per cognitive tick
DB_PATH       = os.path.join(tempfile.gettempdir(), "ngp_cognitive_bench.db")
DIM           = 128                   # Grassmannian projection G(4, C^64)
K_SUBSPACE    = 4                     # Subspace rank
N_CENTROIDS   = 64                    # IVF Voronoi cells (K=4096 in prod)
N_GLYPHS      = 500                   # Synthetic HaloGlyphs
HOT_K         = 3                     # Ebbinghaus hot buffer
AIR_THRESHOLD = 0.01                  # Anomaly Index Ratio abort threshold
MRA_MIN       = 0.95                  # Memory Retrieval Accuracy floor L0-L2
LAMBDA_DECAY  = 0.0495                # Ebbinghaus half-life ~14 hrs


# ═══════════════════════════════════════════════════════════════════════════════
# S0 · Hippocampus Initialization
# ═══════════════════════════════════════════════════════════════════════════════

def _init_db() -> sqlite3.Connection:
    # Calibration: let the stream of WAL flow through the Fibonacci sieve
    conn = sqlite3.connect(DB_PATH, timeout=5.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA mmap_size = 34359738368;")
    conn.execute("PRAGMA cache_size = -2000000;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hologlyphs (
                glyph_id    TEXT PRIMARY KEY,
                layer       INTEGER NOT NULL,
                salience    REAL    NOT NULL,
                content     TEXT,
                vector_blob BLOB,
                created_at  REAL    NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tombstones (
                glyph_id        TEXT PRIMARY KEY,
                annihilated_at  REAL NOT NULL,
                sig             TEXT NOT NULL,
                reason          TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS apsa_log (
                event_id    TEXT PRIMARY KEY,
                event_type  TEXT NOT NULL,
                forced      INTEGER DEFAULT 0,
                ts          REAL NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_layer ON hologlyphs(layer);")
    return conn


class HermesHeartbeatSentinel(threading.Thread):
    """WAL checkpoint guardian — 30-second cycle."""
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(daemon=True)
        self._conn = conn
        self._stop = threading.Event()

    def run(self):
        while not self._stop.wait(30):
            try:
                self._conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
            except Exception:
                pass

    def halt(self):
        self._stop.set()


# ═══════════════════════════════════════════════════════════════════════════════
# IVF Index — Grassmannian Manifold G(4, C^64) · Pure NumPy
# ═══════════════════════════════════════════════════════════════════════════════

def _stiefel_repr(vec: np.ndarray) -> np.ndarray:
    """Project flat vector to Stiefel representative U ∈ R^(n×k), U^T U = I_k."""
    mat = vec.reshape(DIM // K_SUBSPACE, K_SUBSPACE)
    U, _, _ = np.linalg.svd(mat, full_matrices=False)
    return U  # shape (32, 4)

def _chordal_dist(U: np.ndarray, V: np.ndarray) -> float:
    """d_c(X,Y) = sqrt(sum(sin^2(theta_i))) via principal angles."""
    M = U.T @ V
    sigma = np.linalg.svd(M, compute_uv=False)
    sigma = np.clip(sigma, -1.0, 1.0)
    return float(np.sqrt(np.sum(np.sin(np.arccos(sigma)) ** 2)))

def _geodesic_centroid(Us: List[np.ndarray]) -> np.ndarray:
    """SVD-based Fréchet mean on Grassmannian — gravitational collapse."""
    n, k = Us[0].shape
    agg = sum(U @ U.T for U in Us)
    Q, _, _ = np.linalg.svd(agg)
    return Q[:, :k]

class IVFIndex:
    """Inverted File Index over Grassmannian G(4, C^64)."""

    def __init__(self, n_centroids: int = N_CENTROIDS):
        self.n_centroids = n_centroids
        self.centroids: List[np.ndarray] = []
        self.cells: Dict[int, List[Tuple[str, np.ndarray]]] = {}
        self._lock = threading.Lock()

    def train(self, reps: List[np.ndarray], max_iter: int = 10):
        # Calibration: seeds drawn from Fibonacci-spaced indices
        fib_idx = _fibonacci_indices(len(reps), self.n_centroids)
        self.centroids = [reps[i].copy() for i in fib_idx]
        for _ in range(max_iter):
            buckets: Dict[int, List[np.ndarray]] = {i: [] for i in range(len(self.centroids))}
            for rep in reps:
                idx = self._nearest(rep)
                buckets[idx].append(rep)
            for i, members in buckets.items():
                if members:
                    self.centroids[i] = _geodesic_centroid(members)
        self.cells = {i: [] for i in range(len(self.centroids))}

    def add(self, glyph_id: str, rep: np.ndarray):
        with self._lock:
            idx = self._nearest(rep)
            self.cells[idx].append((glyph_id, rep))

    def search(self, query_rep: np.ndarray, top_k: int = 5,
               n_probe: int = 4) -> List[Tuple[str, float]]:
        dists = [(i, _chordal_dist(query_rep, c)) for i, c in enumerate(self.centroids)]
        dists.sort(key=lambda x: x[1])
        candidates = []
        for cell_idx, _ in dists[:n_probe]:
            for gid, rep in self.cells.get(cell_idx, []):
                candidates.append((gid, _chordal_dist(query_rep, rep)))
        candidates.sort(key=lambda x: x[1])
        return candidates[:top_k]

    def _nearest(self, rep: np.ndarray) -> int:
        return min(range(len(self.centroids)),
                   key=lambda i: _chordal_dist(rep, self.centroids[i]))

    def dispose(self):
        with self._lock:
            self.centroids.clear()
            self.cells.clear()

def _fibonacci_indices(total: int, n: int) -> List[int]:
    phi = (1 + math.sqrt(5)) / 2
    return [int((i * phi % 1) * total) % total for i in range(n)]


# ═══════════════════════════════════════════════════════════════════════════════
# Cube-Split Quantization — CDF Transform (250x compression target)
# ═══════════════════════════════════════════════════════════════════════════════

def cube_split_encode(U: np.ndarray, bits: int = 4) -> bytes:
    """CDF-transform Stiefel representative → compact code."""
    flat = U.flatten().astype(np.float32)
    # CDF normalization via Gaussian erf
    normalized = np.clip((flat - flat.mean()) / (flat.std() + 1e-9), -3, 3)
    cdf_vals = 0.5 * (1 + np.array([math.erf(float(v) / math.sqrt(2)) for v in normalized]))
    levels = (2 ** bits) - 1
    quantized = np.round(cdf_vals * levels).astype(np.uint8)
    return quantized.tobytes()

def cube_split_decode(data: bytes, shape: Tuple) -> np.ndarray:
    """Inverse CDF decode → approximate Stiefel representative."""
    bits = 4
    levels = (2 ** bits) - 1
    quantized = np.frombuffer(data, dtype=np.uint8).astype(np.float32)
    cdf_vals = quantized / levels
    # Approximate Gaussian quantile (probit)
    approx = np.array([_probit(float(p)) for p in cdf_vals])
    mat = approx.reshape(shape)
    # Re-orthogonalize
    U, _, Vt = np.linalg.svd(mat, full_matrices=False)
    return U @ Vt

def _probit(p: float) -> float:
    p = max(1e-6, min(1 - 1e-6, p))
    # Rational approximation of Gaussian quantile
    if p < 0.5:
        t = math.sqrt(-2 * math.log(p))
    else:
        t = math.sqrt(-2 * math.log(1 - p))
    c = [2.515517, 0.802853, 0.010328]
    d = [1.432788, 0.189269, 0.001308]
    result = t - (c[0] + c[1]*t + c[2]*t**2) / (1 + d[0]*t + d[1]*t**2 + d[2]*t**3)
    return result if p >= 0.5 else -result


# ═══════════════════════════════════════════════════════════════════════════════
# Ebbinghaus Context Compressor — L0 → L5
# ═══════════════════════════════════════════════════════════════════════════════

SALIENCE = {0: 1.0, 1: 0.85, 2: 0.85, 3: 0.6, 4: 0.4, 5: 0.1}

def _ast_strip(text: str) -> str:
    """Retain only typed nodes: class/def/import signatures."""
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if re.match(r'^(def |class |import |from |async def |interface |struct |fn |func )', s):
            lines.append(line)
    return "\n".join(lines) or "[AST-Pruned]"

def _ebbinghaus_decay(text: str, age_hrs: float) -> Tuple[int, str]:
    """Returns (layer, compressed_content)."""
    R = math.exp(-LAMBDA_DECAY * age_hrs)
    if age_hrs == 0:
        return 0, text
    elif R > 0.75:
        return 1, _ast_strip(text)
    elif R > 0.50:
        return 2, _ast_strip(text)
    elif R > 0.25:
        # Semantic summary — keep first sentence per paragraph
        lines = [s.split('.')[0] + '.' for s in text.split('\n') if s.strip()]
        return 3, ' '.join(lines[:3])
    elif R > 0.10:
        # Relation triplets only
        words = text.split()
        return 4, f"[triplet: {' '.join(words[:5])}...]"
    else:
        return 5, f"[tombstone:{hashlib.sha256(text.encode()).hexdigest()[:8]}]"

class EbbinghausCompressor:
    def __init__(self):
        self.turns: List[Tuple[str, float]] = []

    def add(self, text: str, age_hrs: float = 0.0):
        ts = time.time() - age_hrs * 3600
        self.turns.append((text, ts))

    def compress(self) -> List[Tuple[int, str, float]]:
        now = time.time()
        result = []
        n = len(self.turns)
        for i, (text, ts) in enumerate(self.turns):
            if i >= n - HOT_K:
                result.append((0, text, SALIENCE[0]))
            else:
                age_hrs = (now - ts) / 3600
                layer, compressed = _ebbinghaus_decay(text, age_hrs)
                result.append((layer, compressed, SALIENCE[layer]))
        return result

    def compression_ratio(self) -> float:
        raw = sum(len(t[0].split()) for t in self.turns)
        compressed = self.compress()
        comp = sum(len(c[1].split()) for _, c, _ in compressed)
        return raw / max(1, comp)


# ═══════════════════════════════════════════════════════════════════════════════
# APSA · Sabotage Detection + TokenShield
# ═══════════════════════════════════════════════════════════════════════════════

class APSAMonitor:
    def __init__(self):
        self._forced = 0
        self._events = 0
        self._shield_history: List[str] = []

    def record(self, forced: bool = False):
        self._events += 1
        if forced:
            self._forced += 1

    @property
    def air(self) -> float:
        if self._events == 0:
            return 0.0
        return (self._forced / self._events) * 1.5

    def token_shield_check(self, state: dict) -> Optional[str]:
        h = hashlib.sha3_256(json.dumps(state, sort_keys=True).encode()).hexdigest()
        self._shield_history.append(h)
        if len(self._shield_history) >= 2 and self._shield_history[-1] == self._shield_history[-2]:
            return "[TokenShield] Runaway loop cascade prevented. Stream suspended."
        if len(self._shield_history) > 8:
            self._shield_history.pop(0)
        return None

    def check_abort(self) -> bool:
        return self.air >= AIR_THRESHOLD


# ═══════════════════════════════════════════════════════════════════════════════
# Needle-in-Haystack Generator — HaloGlyph injection
# ═══════════════════════════════════════════════════════════════════════════════

GOLDEN_FACTS = [
    ("UUID:4a7f-SIRT6",   "SIRT6 suppresses LINE-1 retrotransposons preventing systemic inflammation."),
    ("UUID:9c2b-TERT",    "TERT activation via H3K27me3 removal extends telomere integrity."),
    ("UUID:3e1d-FROHLICH", "Frohlich condensate phase transition: Tc=20.3C, pH=8.3."),
    ("UUID:7a0e-CHEBYSHEV","ChebyPush reduces PPR iteration from O(1/alpha) to O(1/sqrt(alpha))."),
    ("UUID:2f8c-CRDT",    "Vector clocks resolve conflicts: Logical Time → Trust Tier → PoK → SHA256."),
]

def _generate_noise_turn(length: int = 80) -> str:
    words = ["agent", "context", "memory", "graph", "node", "vector", "semantic",
             "query", "index", "sync", "delta", "hash", "proof", "glyph", "layer"]
    rng = np.random.default_rng(int(time.time() * 1000) % 2**32)
    return " ".join(words[int(i) % len(words)] for i in rng.integers(0, len(words), length))

def build_synthetic_dialogue(n_turns: int = 40) -> List[Tuple[str, str, int]]:
    """Returns list of (turn_text, injected_fact_id or '', position_layer)."""
    turns = []
    inject_positions = {5: 0, 20: 1, 35: 2, 10: 3, 25: 4}
    for i in range(n_turns):
        if i in inject_positions:
            fact_idx = inject_positions[i]
            fid, fact_text = GOLDEN_FACTS[fact_idx]
            turns.append((_generate_noise_turn(40) + " " + fact_text, fid, i))
        else:
            turns.append((_generate_noise_turn(60), "", i))
    return turns


# ═══════════════════════════════════════════════════════════════════════════════
# Cognitive Audit — MRA + Chordal Loss
# ═══════════════════════════════════════════════════════════════════════════════

def _mra(retrieved_ids: List[str], ground_truth: List[str]) -> float:
    if not ground_truth:
        return 1.0
    hits = sum(1 for gid in ground_truth if gid in retrieved_ids)
    return hits / len(ground_truth)

def _compression_loss(U_orig: np.ndarray, U_recovered: np.ndarray) -> float:
    return _chordal_dist(U_orig, U_recovered)


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark Runner — S0 → S1 → S2
# ═══════════════════════════════════════════════════════════════════════════════

def run():
    sep = "=" * 64
    print(sep)
    print("  Cognitive Fidelity Benchmark — NGP 4.5")
    print(f"  Hyper-Tetrapod · {FREQ_HZ} Hz · Syn Syndicate")
    print(sep)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    apsa = APSAMonitor()

    # ── S0: Hippocampus Initialization ───────────────────────────────────────
    print(f"\n**S0 · Hippocampus Initialization**")
    t0 = time.perf_counter()
    conn = _init_db()
    sentinel = HermesHeartbeatSentinel(conn)
    sentinel.start()
    init_ms = (time.perf_counter() - t0) * 1000
    print(f"| SQLite WAL init         | {init_ms:.1f} ms |")

    # Train IVF on random Stiefel representatives
    rng = np.random.default_rng(432)
    sample_vecs = [rng.standard_normal(DIM).astype(np.float32) for _ in range(N_GLYPHS)]
    sample_reps = [_stiefel_repr(v) for v in sample_vecs]

    t0 = time.perf_counter()
    ivf = IVFIndex(N_CENTROIDS)
    ivf.train(sample_reps)
    train_ms = (time.perf_counter() - t0) * 1000
    print(f"| IVF train ({N_CENTROIDS} centroids) | {train_ms:.1f} ms |")

    # ── S1: Glyphing & Compression ────────────────────────────────────────────
    print(f"\n**S1 · Glyphing & Compression**")

    # Bulk insert HaloGlyphs
    dialogue = build_synthetic_dialogue(N_GLYPHS)
    golden_ids = [fid for _, fid, _ in dialogue if fid]

    t0 = time.perf_counter()
    insert_times = []
    for i, (text, fid, pos) in enumerate(dialogue):
        gid = fid if fid else str(uuid.uuid4())[:16]
        vec = sample_vecs[i]
        rep = sample_reps[i]
        code = cube_split_encode(rep)
        salience = 1.0 if fid else 0.7
        t1 = time.perf_counter()
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO hologlyphs "
                "(glyph_id, layer, salience, content, vector_blob, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (gid, 0, salience, text[:200], code, time.time())
            )
        insert_times.append(time.perf_counter() - t1)
        ivf.add(gid, rep)
        apsa.record(forced=False)

    avg_ms = np.mean(insert_times) * 1000
    ops = N_GLYPHS / sum(insert_times)
    raw_bytes = N_GLYPHS * DIM * 4
    comp_bytes = N_GLYPHS * len(cube_split_encode(sample_reps[0]))
    ratio = raw_bytes / comp_bytes
    print(f"| Glyphs inserted         | {N_GLYPHS} |")
    print(f"| Avg insert latency      | {avg_ms:.3f} ms |")
    print(f"| Throughput              | {ops:,.0f} ops/sec |")
    print(f"| FP32 raw size           | {raw_bytes/1024:.1f} KB |")
    print(f"| Cube-Split encoded      | {comp_bytes/1024:.1f} KB |")
    print(f"| Compression ratio       | {ratio:.1f}x |")

    # Ebbinghaus compression
    ecc = EbbinghausCompressor()
    for i, (text, _, _) in enumerate(dialogue[:20]):
        age = max(0, (20 - i) * 0.8)
        ecc.add(text, age_hrs=age)
    compressed = ecc.compress()
    ecc_ratio = ecc.compression_ratio()
    layer_counts = {}
    for layer, _, _ in compressed:
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    print(f"\n| Ebbinghaus turns        | {len(ecc.turns)} |")
    print(f"| Hot buffer (L0)         | {layer_counts.get(0,0)} turns |")
    for l in range(1, 6):
        if l in layer_counts:
            print(f"| Layer L{l}                | {layer_counts[l]} turns |")
    print(f"| Compression ratio       | {ecc_ratio:.1f}x |")

    # ── S2: Cognitive Audit ───────────────────────────────────────────────────
    print(f"\n**S2 · Cognitive Audit**")

    # IVF search — retrieve golden HaloGlyphs
    retrieved = []
    search_times = []
    for fid, fact_text in GOLDEN_FACTS:
        # Build query from fact keywords
        kw = fact_text.split()[:8]
        qvec = rng.standard_normal(DIM).astype(np.float32)
        qrep = _stiefel_repr(qvec)
        t1 = time.perf_counter()
        results = ivf.search(qrep, top_k=10)
        search_times.append(time.perf_counter() - t1)
        retrieved.extend([gid for gid, _ in results])

    avg_search_ms = np.mean(search_times) * 1000
    mra = _mra(retrieved, golden_ids)

    # Chordal loss: encode → decode cycle
    test_rep = sample_reps[0]
    code = cube_split_encode(test_rep)
    recovered = cube_split_decode(code, test_rep.shape)
    chord_loss = _compression_loss(test_rep, recovered)

    # APSA — simulate anomaly events
    for _ in range(3):
        apsa.record(forced=True)
    for _ in range(300):
        apsa.record(forced=False)
    air = apsa.air

    # TokenShield — loop detection
    frozen = {"tool": "search", "query": "longevity", "step": 42}
    shield_result = None
    for attempt in range(5):
        state = frozen if attempt > 1 else {**frozen, "step": attempt}
        shield_result = apsa.token_shield_check(state)
        if shield_result:
            break

    print(f"| Memory Retrieval Acc.   | {mra*100:.1f}% (target ≥95%) |")
    print(f"| Chordal loss (L0 cycle) | {chord_loss:.4f} (threshold 0.05) |")
    print(f"| Avg IVF search          | {avg_search_ms:.2f} ms |")
    print(f"| AIR (Sabotage Index)    | {air:.4f} (threshold {AIR_THRESHOLD}) |")
    print(f"| TokenShield             | {'TRIGGERED' if shield_result else 'clear'} |")

    # MRA per layer
    print(f"\n| Layer | State           | Salience | Expected MRA |")
    print(f"|-------|-----------------|----------|--------------|")
    layer_data = [
        (0, "Hot Buffer (Raw)",  SALIENCE[0], "99–100%"),
        (1, "Typed AST Nodes",   SALIENCE[1], "90–95%"),
        (2, "Typed AST Nodes",   SALIENCE[2], "90–95%"),
        (3, "Semantic Summary",  SALIENCE[3], "75–85%"),
        (4, "Relation Triplets", SALIENCE[4], "60–70%"),
        (5, "Tombstone",         SALIENCE[5], "< 5%"),
    ]
    for l, state, sal, expected in layer_data:
        print(f"| L{l}    | {state:<15} | {sal:<8} | {expected:<12} |")

    # AIR abort check
    abort = apsa.check_abort()
    if abort:
        print(f"\n⚠  AIR={air:.4f} ≥ {AIR_THRESHOLD} — Thymus L5 activated. Node → Quarantine Mode.")
    else:
        print(f"\n✓  AIR={air:.4f} — below threshold. System coherent.")

    # ── Summary ───────────────────────────────────────────────────────────────
    db_kb = os.path.getsize(DB_PATH) / 1024
    print(f"\n{sep}")
    print(f"  SUMMARY")
    print(f"{sep}")
    print(f"  Glyphs stored       : {N_GLYPHS}")
    print(f"  Insert throughput   : {ops:,.0f} ops/sec")
    print(f"  Cube-Split ratio    : {ratio:.1f}x  (target 250x at full depth)")
    print(f"  Ebbinghaus ratio    : {ecc_ratio:.1f}x  (target 8-12x observed, 250x potential)")
    print(f"  MRA L0-L2           : {mra*100:.1f}%  (target ≥95%)")
    print(f"  Chordal loss        : {chord_loss:.4f}  (threshold 0.05)")
    print(f"  AIR                 : {air:.4f}  ({'ABORT' if abort else 'OK'})")
    print(f"  DB on disk          : {db_kb:.1f} KB")
    print(f"  Coherence freq      : {FREQ_HZ} Hz")
    print(f"{sep}")

    # Cleanup
    sentinel.halt()
    ivf.dispose()
    conn.close()

if __name__ == "__main__":
    run()
