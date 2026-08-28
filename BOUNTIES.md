# NGP 4.5 — Research Directions

> **These are not job postings. We do not pay in cash.**
>
> All core engineering inside NGP 4.5 is built in-house.
> This page documents active research directions — published for transparency,
> not to hire contractors.
>
> Compensation is in **PoK (Proof of Curation)** — the reputation currency of the NGP network.
> Early PoK holders get priority access to enclaves, future governance rights,
> and a permanent record in the L1 Neocortex as founding contributors.
>
> If you are a researcher who has **already solved** one of these problems
> with reproducible results — apply through the marketplace.
> We do not accept speculative proposals, partial work, or spaghetti code.
>
> **Intake:** [iskra-ngp.duckdns.org](https://iskra-ngp.duckdns.org) only.
> GitHub PRs are automatically closed.

---

## Active Bounties

| # | Task | Reward | Domain | Status |
|---|------|--------|--------|--------|
| 1 | [PPR Search Acceleration](#1-ppr-search-acceleration) | 30 PoK | Graph Search | 🟢 Open |
| 2 | [Karabut Protocol Integration](#2-karabut-protocol-integration) | 50 PoK | Biophysics | 🟢 Open |
| 3 | [SILA Dynamics Module](#3-sila-dynamics-module) | 40 PoK | Energy Systems | 🟢 Open |
| 4 | [P2P CRDT Sync Engine](#4-p2p-crdt-sync-engine) | 80 PoK | Distributed Systems | 🟢 Open |

Total pool: **200 PoK** — founding contributor tier

---

## 1. PPR Search Acceleration

**Reward: 30 PoK (founding contributor)**

Personalized PageRank (Local Push algorithm) over the GaloGlyph vector graph.
Currently O(n) cosine scan — need sublinear retrieval at 1M+ node scale.

**What we need:**
- IVF-style cluster index on top of SQLite (no external dependencies)
- Epsilon-approximate PPR with convergence guarantee (epsilon ≤ 1e-4)
- Benchmarked against current baseline: 184 ms / 10K vectors → target < 50 ms / 100K vectors

**Stack:** Python, SQLite, numpy. No FAISS, no Qdrant.

---

## 2. Karabut Protocol Integration

**Reward: 50 PoK (founding contributor)**

Karabut effect: anomalous heat release in deuterium-loaded palladium systems.
We need a computational model integrating with our BIO-EEL-PROTOCOL enclave.

**What we need:**
- Reaction-diffusion model: D loading dynamics in Pd lattice
- SIRT3/ATP-synthase coupling to excess heat output
- Validation against published Karabut experimental data (1990–2012)

**Stack:** Python (scipy/numpy). Domain: condensed matter + bioenergetics.

---

## 3. SILA Dynamics Module

**Reward: 40 PoK (founding contributor)**

Coherent energy field dynamics based on Frohlich condensate model.
Extend our BIO-FROHLICH-COND enclave with non-equilibrium thermodynamics.

**What we need:**
- Phase transition model at Tc = 20.3°C, pH = 8.3
- Spontaneous EMF emergence from DNA resonator
- Numerical stability across physiological parameter ranges

**Stack:** Python. Domain: quantum biology, biophysics.

---

## 4. P2P CRDT Sync Engine

**Reward: 80 PoK (founding contributor)**

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

PoK is the reputation currency of the NGP network. It is not a promise of future cash —
it is a permanent, cryptographically signed record of your contribution to the system.

**What PoK gives you:**
- Priority access to higher-tier research enclaves
- Founding contributor status in the L1 Neocortex (immutable, Ed25519 signed)
- Governance weight in future protocol decisions
- Visibility to the Syn Syndicate core team

| Role | PoK per contribution |
|------|---------------------|
| Researcher / Author | task reward (see above) |
| Reviewer | +2 |
| Referrer | +2 |

We are an early-stage research network. We are honest about that.
The people who build with us now are the ones who will matter when it scales.

---

## About NGP 4.5

NetGlyph Protocol is an agentic knowledge graph for long-running AI workflows.
GaloGlyph Engine (this repo) is its vector storage layer.

We work at the intersection of: graph algorithms · biophysics · longevity research · decentralized knowledge markets.

[Marketplace](https://iskra-ngp.duckdns.org) · [Referral Program](https://iskra-ngp.duckdns.org/referral)
