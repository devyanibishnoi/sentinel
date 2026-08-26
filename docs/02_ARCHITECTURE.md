# Sentinel — System Architecture

**Status:** Draft v1.1
**Owner:** Devyani Bishnoi

---

## 1. Design principles

- **The Detection is the contract.** One schema between components.
- **Baselines before cleverness**, at population and entity level.
- **Everything reproducible.** Config in, dataset hash logged.
- **The `Scorer` protocol is the leverage point.** `fit`/`score`, entity-aware.
- **Entity is an explicit axis.** Every score answers "how unusual for this entity," not just "how unusual in general."
- **Explainable, bounded, gated.** Every detection shows its driving signal. Every automated decision has a confidence gate and an audit record, including refusals.
- **The demo is never the evaluation.** The scored numbers come from the public benchmark's held-out test set, full stop. The Razorpay-shaped stream demonstrates portability, never contributes a metric.

## 2. Pipeline

```
   IEEE-CIS Fraud Detection (sampled)        Synthetic Razorpay-shaped stream
              │                                          │
              ▼                                          ▼
   ┌─────────────────────────┐            ┌─────────────────────────┐
   │ 1. Ingestion + Entity     │            │ 1b. Demo Adapter          │
   │    Reconstruction         │            │   (same Event schema,      │
   └────────────┬─────────────┘            │    illustrative only)      │
                │                          └────────────┬─────────────┘
                │ feature vectors, keyed by entity_id     │
                ▼                                        │
   ┌─────────────────────────┐                          │
   │ 2. Detection Engine       │◄─────────────────────────┘
   │  population baseline      │   (scores the demo stream with the
   │  + per-entity baseline    │    already-trained model, no retraining,
   │  + IsolationForest         │    no metric contribution)
   └────────────┬─────────────┘
                │ Detection (population + entity-deviation scores)
     ┌──────────┼───────────────┐
     ▼          ▼               ▼
 ┌────────┐ ┌──────────┐ ┌──────────────┐
 │3. Typo-│ │4. Ring     │ │5. Gated       │
 │  logy   │ │   Detection │ │   Auto-        │
 │  Tags    │ │   (graph,    │ │   Responder     │
 │          │ │   connected  │ │   allow/review/ │
 │          │ │   components)│ │   decline        │
 └────────┘ └──────────┘ └──────────────┘
                │
                ▼
       results store (Parquet/CSV) + audit log
                │
                ▼
   ┌─────────────────────────┐
   │ 6. Risk Console            │
   │  FastAPI + HTMX             │
   │  detection feed, explain     │
   │  panel, metrics view,         │
   │  ring viewer, audit trail      │
   └─────────────────────────┘
```

## 3. Component responsibilities

**Ingestion & Entity Reconstruction** — unchanged from prior revision. Loads a stratified IEEE-CIS sample, derives `entity_id`, sanity-checks it before anything trusts it.

**Demo Adapter (new)** — produces synthetic transactions in the same `Event` schema as the real adapter, shaped like a real payment gateway transaction (method, amount in the smallest currency unit, timestamp, entity), with a small injected ring (a handful of entities deliberately sharing a device/card fingerprint) so it's reliably catchable on camera. Never used for training or for the scored evaluation, only for scoring with the already-fit model, live, in the console.

**Detection Engine** — unchanged core idea: population deviation plus entity deviation, combined into one score, IsolationForest doing the heavy lifting on the combined feature set.

**Typology Tagging** — unchanged: descriptive, unscored, rule-based (device mismatch, amount deviation, cold start).

**Ring Detection (now core)** — shared-fingerprint graph, `networkx` connected components, proxy fraud-rate evaluation with the ground-truth caveat stated everywhere it's shown.

**Gated Auto-Responder (now core)** — on a Detection above a confidence threshold, decides allow / review / decline based on score and a simple exposure proxy (transaction amount standing in for blast radius). Every decision, including a decision *not* to act, writes an audit record: score, threshold, entity, reasoning.

**Risk Console (new, see `06_FRONTEND_AND_DEMO.md` for the full spec)** — reads from the results store and audit log. Not a separate service with its own state; a thin read view, same instinct as the original project's ADR-0002.

## 4. Core data contract — `Detection`

```jsonc
{
  "detection_id": "uuid",
  "schema_version": "1.1",
  "timestamp": "ISO-8601",
  "source": "benchmark|demo",              // which pipeline produced this, never mixed in reporting
  "entity": { "type": "proxy_account", "id": "string" },
  "score_population": 0.0,
  "score_entity_deviation": 0.0,
  "score_combined": 0.0,
  "threshold": 0.0,
  "detector": { "name": "string", "version": "string", "config_hash": "string" },
  "evidence": { "features": {} },
  "typology_tag": "string|null",
  "ring_cluster_id": "string|null",
  "decision": "allow|review|decline|null",
  "decision_reasoning": "string|null",
  "labels": { "ground_truth": "benign|fraud|null" }
}
```

The new `source` field is what enforces the "demo is never the evaluation" principle at the schema level, not just as a convention someone has to remember.

## 5. Tech stack

- **Core language: Python.** scikit-learn, pandas.
- **Graph: networkx**, for ring detection.
- **Frontend: FastAPI + HTMX**, server-rendered templates, no separate build pipeline. Same reasoning as the original project's ADR-0002: one language, no API-contract drift, the entire time budget stays on the detection engine and the console's clarity, not a frontend framework.
- **Storage:** Parquet/CSV results store, a CSV or SQLite audit log (SQLite if the auto-responder's decision volume makes CSV awkward to query from the console; decide empirically, don't over-plan it).

## 6. What's still cut

No live payment-gateway integration, no multi-tenant auth, no LLM/RAG enrichment layer, no deployed infrastructure beyond a local run. The console runs locally for the demo video; it does not need to be hosted anywhere.

## 7. Fallback path

If entity reconstruction doesn't pass its sanity check, fall back to a coarser entity proxy, report the entity-behavior signal as weaker but present, and keep the rest of the architecture, including the console and ring detection, unchanged; they operate on whatever entity key ends up being trustworthy.
