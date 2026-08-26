# Sentinel — Product Requirements Document

**Status:** Draft v1.1
**Owner:** Devyani Bishnoi

---

## 1. Summary

Sentinel learns what normal behavior looks like for a specific account, card, or device, and scores deviations from that baseline. This is a security technique, UEBA (User and Entity Behavior Analytics), applied to payments fraud: a transaction that's unremarkable in the general population can still be a strong signal of account takeover or coordinated abuse if it's out of character for that specific entity. Detections are explainable, gated, and viewable in a live console, not buried in a notebook.

## 2. Problem statement

Digital payment fraud in India is real and growing fast, not a hypothetical: RBI's own data shows digital payment fraud value jumped more than fivefold to Rs 14.57 billion (about $175 million) in the year ended March 2024, and a LocalCircles survey found close to half of urban Indian households have experienced financial fraud in the last three years, 43% of them credit card fraud and 30% UPI fraud. A flat "is this transaction fraud" classifier misses the cases that matter most: a stolen card used for a normal-looking amount, or a new account behaving identically to nine other "new" accounts sharing one device. There is no public, labeled Indian-payments dataset to train or evaluate against directly, almost certainly for the same regulatory and privacy reasons no public SOC telemetry exists either. This project is upfront about that gap rather than pretending it doesn't exist.

## 3. Class of loss

**Account-level behavioral fraud, with abuse-ring detection and a gated auto-responder built as core capabilities on the same entity model**, not as afterthoughts. This directly answers three of the track's four example directions (fraud-spike detector, abuse-ring sentinel, and the "auto-responder" shape the bar explicitly allows) from one underlying engine. Chargeback-evidence and return-risk remain out of scope, documented as open extensions (§9).

## 4. Goals and non-goals

**Goals**
- Build per-entity behavioral baselines and score deviation from each entity's own history, alongside population-level scoring.
- Detect clusters of accounts sharing device/card fingerprints at a suspicious rate (ring detection), as a core capability.
- Gate high-confidence detections into an auto-responder (allow / review / decline) with a full, inspectable audit trail.
- Make every detection explainable: which signal drove it, at a glance, in a live console.
- Measure precision, recall, and FPR against explicit baselines, both population-level and entity-level, on a real held-out test set.
- Demonstrate the engine against a live, Razorpay-shaped synthetic stream, clearly separated from and never blended into the scored evaluation.
- Every result reproducible from a config and a dataset hash.

**Non-goals**
- Not a production fraud engine or a live payment-gateway integration. The Razorpay-shaped demo stream is synthetic, illustrative, and clearly labeled as such.
- Not real-time streaming at scale.
- Not chargebacks or returns in this build.
- Not a verified ground-truth ring dataset; ring evaluation uses a derived proxy label (§8), reported as approximate.
- Not a multi-tenant production console. The Risk Console (see `06_FRONTEND_AND_DEMO.md`) is a focused demo and inspection tool, not a hardened product.

## 5. Users / personas

**Primary — Risk analyst.** Needs to see what's flagged, why it's out of character *for that account*, and how confident, fast enough to act or escalate. Cares about false-positive rate above all.

**Secondary — the reviewer.** Cares whether the entity-baseline framing is real and defensible, and whether the console makes the rigor visible in under a minute rather than requiring a CSV to be read line by line.

## 6. Success metrics

| Metric | Definition | Target framing |
|---|---|---|
| Detection rate (recall) | True fraud flagged, population and entity-deviation level | Report both, and whether entity-level catches cases population-level misses |
| False-positive rate | Benign flagged as fraud | Report at multiple operating points |
| PR-AUC | Primary, given class imbalance | Reported for population-only, entity-only, and combined scorers |
| Ring-cluster precision | Fraction of flagged clusters with an elevated proxy fraud rate | Explicitly caveated as a derived, not ground-truth, label |
| Auto-responder coverage | % of high-confidence detections resolved without escalation | Descriptive, with full audit trail |
| Explainability | Every detection in the console shows its driving signal(s) | Binary: present or not, no partial credit |
| Reproducibility | Any number re-runnable from a config | 100% |

## 7. Scope for this build

**Core (must ship):**
- Proxy account ID reconstruction (documented as approximate, §8), with the India-context framing above.
- Baselines: random/prior, rule-based (population and entity level), statistical (population and entity z-score).
- IsolationForest on combined population + entity-deviation features, held-out evaluation, the lift check.
- Ring detection: shared-fingerprint graph, connected components, proxy-label evaluation.
- Gated auto-responder: allow / review / decline, full audit log.
- Risk Console (see `06_FRONTEND_AND_DEMO.md`): detection feed, explain panel, metrics view, ring viewer, audit trail.
- Razorpay-shaped demo stream, clearly separated from scored results.

**Explicitly not core, cut first if the timeline slips:**
- Autoencoder (only if IsolationForest leaves clear headroom).
- Cross-dataset generalization check against a second dataset slice.
- Any console feature beyond the five listed above (no user accounts, no settings, no multi-merchant view).

## 8. Open questions

- Proxy account ID is not verified ground truth; needs the sanity check in the Data & Eval doc before anything downstream trusts it.
- Ring ground truth doesn't exist; cluster proxy fraud rate is a stand-in, reported as such everywhere.
- Whether chargeback-evidence or return-risk are worth a second pass later.

## 9. Key risks

- **Dataset rabbit hole.** Time-boxed explicitly in the Roadmap.
- **Proxy identity risk.** Documented fallback to a coarser entity key if reconstruction doesn't hold up.
- **Scope creep on the console.** Five features, no more, listed explicitly in §7, so "topnotch" means those five done well, not an unbounded feature list.
