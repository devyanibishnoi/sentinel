# Sentinel

**Behavioral fraud detection for payments** — detection by deviation from learned account behavior, not by matching known rules. Explainable, gated, and viewable live in a console, not buried in a notebook.


---

## Why this exists

A flat "is this transaction fraud" classifier misses the cases that matter most: a stolen card used for an ordinary-looking amount, or a new account behaving identically to nine other "new" accounts sharing one device. Both look fine at the population level. Neither looks fine once you ask "is this normal for this entity specifically." This is a security technique (UEBA, User and Entity Behavior Analytics) applied to payments, and it's built to answer, at a glance, why any given transaction was flagged.

## The thesis in one line

*Learn what's normal for this account. Flag what isn't. Explain every flag. Measure the false-positive cost honestly.*

## Documentation

| Doc | What it covers |
|---|---|
| [PRD](docs/01_PRD.md) | Problem, users, success metrics, scope & non-goals |
| [Architecture](docs/02_ARCHITECTURE.md) | Components, the `Detection` contract, tech stack |
| [Data & Evaluation](docs/03_DATA_AND_EVALUATION.md) | Dataset, entity reconstruction, baselines, metrics |
| [Technical Design Specs](docs/04_TECHNICAL_DESIGN_SPECS.md) | Per-subsystem interfaces and logic |
| [Roadmap](docs/05_ROADMAP.md) | Day-by-day, time-boxed delivery plan |
| [Risk Console & Demo Layer](docs/06_FRONTEND_AND_DEMO.md) | The five console features, and the demo/benchmark separation |
| [ADRs](docs/ADR_LOG.md) | Why the key decisions were made |
| [Learning Log](docs/LEARNING_LOG.md) | Running notebook of concepts learned while building |

## Subsystems

1. **Ingestion & Entity Reconstruction** — normalizes transactions, derives a proxy account identity
2. **Detection Engine** — population-level and per-entity behavioral deviation scoring
3. **Typology Tagging** — descriptive, unscored labels (device mismatch, amount deviation, cold start)
4. **Ring Detection** — shared-fingerprint clustering across entities
5. **Gated Auto-Responder** — allow / review / decline, with a complete audit trail
6. **Risk Console** — detection feed, explain panel, metrics view, ring viewer, audit trail
7. **Demo Layer** — a Razorpay-shaped synthetic stream, always visually separated from scored results

## Design principles

- The `Detection` schema is the contract between components.
- No result exists without a config that regenerates it.
- Baselines before cleverness, at both the population and entity level.
- Entity is the axis: every score means "how unusual for the entity it belongs to," not just "how unusual in general."
- Explainable, bounded, gated: no detection without a reason, no automated action without an audit record, including refusals.
- The demo is never the evaluation. The scored numbers come from one place, always.

## Status

Design complete, in build (see [Roadmap](docs/05_ROADMAP.md) for the day-by-day plan).
