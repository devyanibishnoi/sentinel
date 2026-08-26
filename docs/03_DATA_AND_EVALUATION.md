# Sentinel — Data & Evaluation Specification

**Status:** Draft v1.1
**Owner:** Devyani Bishnoi

> This is the most important document in the project. Everything else exists to produce numbers this spec defines. Evaluation is designed before models, and the scored numbers only ever come from one place (§7).

---

## 1. Dataset

**Primary: IEEE-CIS Fraud Detection (Kaggle/Vesta).** Has card, address, and device/identity fields, needed to reconstruct a proxy account and support per-entity baselining.

**Watch-outs:** large (590k+ rows, two files to join). Work from a stratified sample, not the full set (see Roadmap time-box).

**Fallback: Credit Card Fraud Detection (ULB/Kaggle).** Coarser, session-level entity proxy, used only if proxy-account reconstruction doesn't hold up.

**Demo-only, never scored: synthetic Razorpay-shaped stream.** Generated, not collected, with a small injected ring for the console demo. See `06_FRONTEND_AND_DEMO.md`. This never appears in any metric in this document.

## 2. Proxy account reconstruction

Unchanged from prior revision: combine card fingerprint and billing address fields, sanity-check the transactions-per-entity distribution and cluster sizes before trusting it, fall back per Architecture §7 if it doesn't hold up.

## 3. Preprocessing contract

Adapter normalizes schema, not values. Scaling fit on train split only, split at the entity level, an entity's transactions stay entirely in train or entirely in test.

## 4. Baselines (mandatory, at two levels)

1. Random / prior baseline.
2. Rule baseline, population level (amount/time thresholds).
3. Rule baseline, entity level (device never seen before for this entity, amount far outside this entity's own range).
4. Statistical baseline, both levels (z-score, population and per-entity).

Every model reports its numbers next to all four, always.

## 5. Models

- **IsolationForest**, required, trained on combined population + entity-deviation features. The central check: does adding entity-deviation features measurably improve PR-AUC over population-only.
- **Ring detection**, required (promoted from stretch): connected components over the shared-fingerprint graph, evaluated against a derived proxy label.
- **Autoencoder**, optional, only if IsolationForest leaves clear headroom.

## 6. Metrics

- Recall, FPR, precision, F1: reported for population-only, entity-only, and combined scorers.
- PR-AUC primary, ROC-AUC secondary.
- Ring-cluster proxy fraud rate, always reported with the ground-truth caveat.
- Auto-responder coverage: % of high-confidence detections resolved without human escalation, descriptive.

## 7. Evaluation protocol

- Entity-level train/test split, not row-level.
- Threshold selected on a held-out validation slice, never test.
- **The scored evaluation runs exclusively on the primary (or fallback) dataset's held-out test set.** The demo stream is a separate, unscored pipeline; no number from it is ever reported alongside a precision/recall/FPR claim. This is enforced by the `source` field on every `Detection` (Architecture §4), not left to memory.
- One config, one logged run.

## 8. Anti-goals in evaluation

- No reporting best-threshold-in-hindsight as operational.
- No train/test leakage, including entity-level leakage from a naive row split.
- No single-dataset claims of generality unless a generalization check is attempted and reported.
- No dropped negative results.
- No treating the ring-cluster proxy label as verified ground truth.
- **No blending demo-stream results into any scored claim, anywhere, including the video.**
