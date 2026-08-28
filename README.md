# GaloGlyph Engine — SQLite-Vector

**Millions of vectors on a 2 GB RAM VPS. No GPU. No Qdrant. No Milvus.**

A production-ready vector store built entirely on SQLite with WAL mode, mmap, and FP8 block microscaling. Part of the NetGlyph Protocol (NGP) stack.

---

## Why SQLite?

The vector-database market assumes you have a dedicated server, a DevOps team, and budget for Qdrant/Milvus/Pinecone. Most AI applications do not. GaloGlyph Engine proves that SQLite — with the right PRAGMA tuning and a custom compression layer — can handle millions of semantic vectors on commodity hardware.

| Metric | GaloGlyph (SQLite) | Qdrant (typical) |
|---|---|---|
| RAM required | 2 GB VPS | 8+ GB recommended |
| GPU required | No | Optional |
| Dependencies | numpy only | Docker + Qdrant server |
| Storage per 128-dim vector | 129 bytes (FP8) | 512 bytes (FP32) |
| Setup time | pip install numpy | docker pull + config |

---

## Architecture

### 1. ThreadSafeNeocortex

The core SQLite engine with production-grade PRAGMA tuning:

```python
conn.execute("PRAGMA journal_mode = WAL;")
conn.execute("PRAGMA synchronous = NORMAL;")
conn.execute("PRAGMA mmap_size = 34359738368;")   # 32 GB virtual mapping
conn.execute("PRAGMA cache_size = -2000000;")     # 2 GB page cache
conn.execute("PRAGMA busy_timeout = 5000;")
```

WAL mode enables concurrent reads during writes. mmap lets the OS handle page caching. The 32 GB virtual mapping costs nothing on RAM — it is just address space.

### 2. FP8 Block Microscaling (MX-Standard)

Each 128-dimensional float32 vector (512 bytes) is compressed to 129 bytes — a 4x reduction — using block-scaled 8-bit quantization:

```python
# Per BLOCK_B=128 elements:
# 1 byte  — shared block scale (log2-quantized exponent)
# N bytes — int8 quantized values

scale_exp = int(math.log2(max_val + 1e-9) + 127)  # stored as uint8
q = int(v / max_val * 127)                         # stored as int8
```

This matches the MX (Microscaling) standard used in modern AI accelerators. The block-shared scale prevents the catastrophic precision loss of naive int8 quantization.

**Storage math for 1M vectors:**
- FP32 naive: 512 MB
- FP8 MX block: 129 MB
- Savings: 383 MB

### 3. Cosine Similarity Search

Pure Python cosine search over the full table — no ANN index, no HNSW, no IVF. For datasets up to ~100K vectors this is fast enough on modern hardware:

```
Search over 10,000 glyphs: ~180 ms on a single-core VPS
```

For larger datasets, add SQLite FTS5 pre-filtering to reduce the candidate set before cosine scoring.

### 4. Ebbinghaus Context Compressor

Conversation context management based on the Ebbinghaus forgetting curve:

- **Hot buffer (K=3)**: last 3 turns at 100% fidelity
- **Mid buffer**: older turns with fidelity > 0.25 compressed to AST signatures (25% of original tokens)
- **Cold buffer**: tombstones (3 tokens each)

Decay function: R(t) = e^(-lambda * t), where lambda = 0.0495 (half-life ~14 hours)

Typical compression ratio: **8-12x** on long conversations.

### 5. TokenShield — Loop Cascade Prevention

Detects runaway agent loops by comparing rolling SHA-256 hashes of the agent state:

```python
h = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
if self.history[-1] == self.history[-2]:
    # suspend stream
```

Two identical consecutive states = frozen loop = stream suspended.

---

## Benchmark Results

Run on a 2 GB RAM VPS (single core, no SSD RAID):

```
============================================================
  GaloGlyph Engine - Live Benchmark
  SQLite-Vector, NGP v3.0
============================================================

[1] DB init with WAL+mmap:         4.2 ms

[2] Inserting 10,000 FP8-compressed vectors...
    Avg insert:    2.847 ms/op
    Throughput:    351 ops/sec
    DB size:       1,312.0 KB
    Raw FP32 est:  5,000.0 KB  (4x larger)
    Compression:   ~4x (FP8 MX-Standard)

[3] Cosine similarity search (top-5)...
    Search over 10,000 glyphs: 184.3 ms
    [0.9823] a3f1... - concept_4721
    [0.9817] b2c4... - concept_1893
    ...

[4] Ebbinghaus Context Compressor...
    Turns:             20
    Hot buffer:        3 (100% fidelity)
    Cold/tombstoned:   17 (9 tombstones)
    Raw tokens:        1,240
    Compressed:        152
    Compression ratio: 8.2x

[5] TokenShield - loop cascade detection...
    Loop detected at attempt 3:
    [TokenShield] Runaway loop cascade prevented. Stream suspended.

============================================================
  SUMMARY
============================================================
  Vectors stored:      10,000
  Insert throughput:   351 ops/sec
  Search latency:      184.3 ms over 10,000 vectors
  FP8 compression:     4x  (512B to 129B per vector)
  Context compression: 8.2x
  DB file:             1,312.0 KB on disk

  Run on any VPS with 2GB RAM. No GPU. No Qdrant. No Milvus.
============================================================
```

---

## Quick Start

```bash
pip install numpy
python galoglyph_demo.py
```

No other dependencies. The demo creates a temporary SQLite database in /tmp, runs all 5 benchmarks, and exits cleanly.

---

## Schema

```sql
CREATE TABLE glyphs (
    node_id        TEXT PRIMARY KEY,
    tenant_id      TEXT NOT NULL,
    concept_name   TEXT NOT NULL,
    salience_score REAL DEFAULT 1.0,
    content_hash   TEXT NOT NULL,
    is_archived    INTEGER DEFAULT 0,
    created_at     REAL NOT NULL
);

CREATE TABLE glyph_faces (
    glyph_id   TEXT NOT NULL,
    face_type  TEXT NOT NULL CHECK(face_type IN
               ('research','code','business','versions','entity')),
    content    TEXT,
    embedding  BLOB,   -- FP8 compressed bytes
    PRIMARY KEY (glyph_id, face_type),
    FOREIGN KEY (glyph_id) REFERENCES glyphs(node_id) ON DELETE CASCADE
);
```

Multi-tenant by design. The `tenant_id` index means each tenant's vectors are isolated at query time without separate databases.

---

## Production Notes

**Concurrent writes**: The threading.Lock in ThreadSafeNeocortex serializes writes. For true write concurrency, shard by tenant across multiple SQLite files.

**Scale limit**: Cosine search is O(n) — expect ~2s at 100K vectors, ~20s at 1M. For 1M+ vectors, add an IVF-style cluster index: cluster at insert time, search only matching clusters.

**Persistence**: WAL files accumulate. Run `PRAGMA wal_checkpoint(TRUNCATE)` periodically or after bulk inserts.

**Memory**: The 32 GB mmap is virtual address space, not RAM. Actual RAM usage scales with your working set, not the mmap size.

---

## Part of NetGlyph Protocol

GaloGlyph Engine is the vector storage layer of the NetGlyph Protocol (NGP) — an agentic knowledge graph system for long-running AI workflows.

- **Glyphs** = semantic knowledge nodes with multi-face content (research, code, business, versions, entity)
- **Salience scoring** = PageRank-like importance weighting
- **Ebbinghaus decay** = automatic archival of low-salience, stale knowledge
- **TokenShield** = loop prevention for autonomous agent swarms

---

## License

MIT
