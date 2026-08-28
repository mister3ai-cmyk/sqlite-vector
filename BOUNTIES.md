# NGP 4.5 — Open Bounties

We publish research and engineering challenges from the NetGlyph Protocol stack.
All work is validated and paid through the NGP marketplace — not via GitHub PRs.

---

## Active Bounties

| # | Task | Reward | Domain | Status |
|---|------|--------|--------|--------|
| 1 | [PPR Search Acceleration](#1-ppr-search-acceleration) | $300 USDC | Graph Search | 🟢 Open |
| 2 | [Karabut Protocol Integration](#2-karabut-protocol-integration) | $500 USDC | Biophysics | 🟢 Open |
| 3 | [SILA Dynamics Module](#3-sila-dynamics-module) | $400 USDC | Energy Systems | 🟢 Open |
| 4 | [P2P CRDT Sync Engine](#4-p2p-crdt-sync-engine) | $800 USDC | Distributed Systems | 🟢 Open |

Total bounty pool: **$2,000 USDC**

---

## 1. PPR Search Acceleration

**Reward: $300 USDC + 15 PoK**

Personalized PageRank (Local Push algorithm) over the GaloGlyph vector graph.
Currently O(n) cosine scan — need sublinear retrieval at 1M+ node scale.

**What we need:**
- IVF-style cluster index on top of SQLite (no external dependencies)
- Epsilon-approximate PPR with convergence guarantee (epsilon ≤ 1e-4)
- Benchmarked against current baseline: 184 ms / 10K vectors → target < 50 ms / 100K vectors

**Stack:** Python, SQLite, numpy. No FAISS, no Qdrant.

---

## 2. Karabut Protocol Integration

**Reward: $500 USDC + 20 PoK**

Karabut effect: anomalous heat release in deuterium-loaded palladium systems.
We need a computational model integrating with our BIO-EEL-PROTOCOL enclave.

**What we need:**
- Reaction-diffusion model: D loading dynamics in Pd lattice
- SIRT3/ATP-synthase coupling to excess heat output
- Validation against published Karabut experimental data (1990–2012)

**Stack:** Python (scipy/numpy). Domain: condensed matter + bioenergetics.

---

## 3. SILA Dynamics Module

**Reward: $400 USDC + 18 PoK**

Coherent energy field dynamics based on Frohlich condensate model.
Extend our BIO-FROHLICH-COND enclave with non-equilibrium thermodynamics.

**What we need:**
- Phase transition model at Tc = 20.3°C, pH = 8.3
- Spontaneous EMF emergence from DNA resonator
- Numerical stability across physiological parameter ranges

**Stack:** Python. Domain: quantum biology, biophysics.

---

## 4. P2P CRDT Sync Engine

**Reward: $800 USDC + 35 PoK**

Decentralized peer-to-peer CRDT synchronization layer for Swarm Memory (Роевая Память) in NGP 4.5.
Zero central coordinator. Conflict-free merge over a distributed knowledge graph via Vector Clocks.

**Core requirements:**

- **Vector Clock Model** on SQLite transactional core — logical time map for all swarm agents
- **4-step conflict resolution:** Logical Time → Trust Tier (architect > builder > contributor > stranger) → PoK Balance (λ-decay 0.0495) → SHA-256 content hash tiebreaker
- **Tombstone Registry** — immutable deletion registry with Ed25519 veto signatures; absolute priority over any write operation
- **NoveltyVN security module:** blocked patterns (eval/exec/os.system → permanent ban, obfuscated Base64 → PoK zeroing), Mock SSE injection neutralization, TokenShield loop detection via BLAKE3 rolling hashes
- **Sabotage Index monitoring:** S_index = (A_forced / F_events) × 1.5; S_index ≥ 0.7 → Quarantine Mode
- **WAL checkpoint** background service every 30 seconds (HermesHeartbeatSentinel pattern)

**Performance target:** 12,000+ transactions/second under concurrent write load.

**SQLite schema (provided):**
```sql
CREATE TABLE p2p_vector_clocks (
    agent_id    TEXT PRIMARY KEY,  -- Ed25519 PubKey
    clock_value INTEGER DEFAULT 0,
    trust_tier  TEXT CHECK(trust_tier IN ('architect','builder','contributor','stranger')),
    last_sync   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE p2p_transaction_deltas (
    glyph_id        TEXT PRIMARY KEY,
    origin_agent_id TEXT,
    vector_state    BLOB,   -- serialized vector clock at creation time
    payload_blob    BLOB,   -- quantized delta (Cube-Split CDF)
    signature       BLOB,   -- Ed25519 (L0 Hardware Fallback)
    FOREIGN KEY (origin_agent_id) REFERENCES p2p_vector_clocks(agent_id)
);
```

**E2E test suite required (Docker, 256 MB RAM limit):**
- NetSplit simulation: node isolation + parallel conflicting HaloGlyph writes
- Vector merge: reconnect + automatic logical time merge
- PoK decay: reputation degradation after 14-day idle simulation
- NoveltyVN breach: shutil.rmtree injection attempt + Mock SSE detection
- Tombstone veto: resurrection attempt on tombstoned node

**Stack:** Python, SQLite, cryptography (Ed25519), Docker. No external databases.

---

## How to Apply

1. Open the NGP Marketplace → [iskra-ngp.duckdns.org](https://iskra-ngp.duckdns.org)
2. Go to tab **📥 Order / Заказать**
3. Describe your approach and timeline
4. We review within 48 hours

**GitHub PRs for bounty work are not accepted.**
All intake, review, and payment happens through the marketplace.

---

## Proof of Curation (PoK)

Every completed bounty earns PoK points — the reputation currency of the NGP network.
PoK unlocks access to higher-tier enclaves and future governance rights.

| Role | PoK per bounty |
|------|---------------|
| Researcher / Author | +5 base + task bonus |
| Reviewer | +2 |
| Referrer | +2 |

---

## About NGP 4.5

NetGlyph Protocol is an agentic knowledge graph for long-running AI workflows.
GaloGlyph Engine (this repo) is its vector storage layer.

We work at the intersection of: graph algorithms · biophysics · longevity research · decentralized knowledge markets.

[Marketplace](https://iskra-ngp.duckdns.org) · [Referral Program](https://iskra-ngp.duckdns.org/referral)
