# Architecture Decision Records

ADRs capture *why* a decision was made, the alternatives, and the tradeoffs, so future-you (or a reviewer) doesn't have to reverse-engineer intent.

---

## Template

```
# ADR-NNNN: <title>
Status: proposed | accepted | superseded by ADR-XXXX
Date: YYYY-MM-DD
Context: what forces are at play?
Decision: what we're doing.
Consequences: what this makes easy, what it makes hard, what we're accepting.
Alternatives considered: and why not.
```

---

# ADR-0001: Class of loss: account-level behavioral fraud, not isolated transaction scoring

**Status:** accepted · **Date:** 2026-08-26

**Context:** Payments fraud-detection work commonly spans several valid directions: chargeback evidence, return-risk scoring, fraud-spike detection, abuse-ring detection. A flat "is this transaction fraud" classifier can look sufficient on paper, but it throws away the most defensible signal available: whether a transaction is normal for the specific account it belongs to.

**Decision:** build the detector around per-entity behavioral baselines (UEBA: User and Entity Behavior Analytics), not just population-level anomaly scoring. Every transaction gets scored twice: how unusual is this in general, and how unusual is this for this specific account. Abuse-ring detection is treated as a direct extension of the same entity model (shared fingerprints across accounts) rather than a separate system, covering two distinct fraud-detection directions from one engine.

**Consequences:** requires a dataset with a real or reconstructable entity identifier, which rules out simpler anonymized transaction datasets and adds real preprocessing work. In exchange, produces a detector that catches account-takeover-style fraud a population-only model misses entirely, and gives a genuinely defensible answer to why this looks like security work applied to a fintech problem, not just a fraud classifier with a new coat of paint.

**Alternatives considered:**
- *Flat population-level classifier:* simpler, faster to build, can look sufficient on paper, but has no answer for why it's a distinctive approach versus any other fraud model, and can't extend cleanly into ring detection.
- *Chargeback-evidence or return-risk as the primary loss type:* both valid directions, but neither has the same natural entity-behavior framing, and public dataset support for them is weaker.

---

# ADR-0002: Entity reconstruction and dataset choice: IEEE-CIS over an anonymized transaction set

**Status:** accepted · **Date:** 2026-08-26

**Context:** Per-entity baselining (ADR-0001) requires knowing which transactions belong to the same account. Fully anonymized, PCA-transformed transaction datasets have no such identifier at all.

**Decision:** use IEEE-CIS Fraud Detection as the primary dataset, and reconstruct a proxy account identity by combining stable card and address fields. Validate this reconstruction with an explicit sanity check (transactions-per-entity distribution, no absurdly large clusters) before anything downstream depends on it. A simpler, anonymized dataset (ULB Credit Card Fraud) is kept as a named fallback with a coarser, session-level entity proxy if the reconstruction doesn't hold up.

**Consequences:** meaningfully more preprocessing risk and effort than an anonymized single-file dataset would require. Proxy identity reconstruction is a known but approximate technique, not verified ground truth, and this is documented everywhere it matters rather than glossed over. In exchange, this is the only path that actually supports the project's core premise; without it, the entity-behavior story has nothing to baseline against.

**Alternatives considered:**
- *ULB Credit Card Fraud as primary:* clean, fast, no preprocessing burden, but has no entity identifier at all, so per-entity baselining isn't possible. Demoted to fallback status.
- *Synthetic account-behavior generator:* avoids the proxy-identity risk entirely, but loses the "real, defensible, held-out test set" framing this project is built around. Kept as a fallback-of-the-fallback if IEEE-CIS proves unworkable in the available time.

---

# ADR-0003: Core stack and scope cuts for the build window

**Status:** accepted · **Date:** 2026-08-26

**Context:** The full space of what a mature fraud-risk platform could include (dashboard, LLM-based enrichment, gated response automation, live feeds) is much larger than what a time-boxed build window supports.

**Decision:** Python core (scikit-learn, pandas), no dashboard, no LLM/RAG enrichment layer, no SOAR-style response infrastructure, no live data feeds. `networkx` is the one addition, for the ring-detection stretch goal, chosen for being lightweight with no new infra required. Results are reported via a script or notebook and a markdown results table, not a deployed service.

**Consequences:** keeps the entire time budget on the detection engine and its evaluation, which is where the actual signal lives. Accepts that the deliverable won't look like a finished product at this stage, which is fine: a repo that runs and an honest account of what broke matters more early on than a polished UI. (Superseded in part by ADR-0005, a console did eventually get built, once the engine and its evaluation were solid first.)

**Alternatives considered:**
- *A minimal dashboard:* would help demo the results visually, but a clean results table and a walked-through notebook cover the same need without the build cost, at this stage of the project. Not pursued yet.
- *LLM-based typology enrichment:* tempting given prior RAG experience, but the descriptive rule-based typology tagger (TDS-3) already satisfies the "explain the flag in plain language" need without adding a new dependency and a new failure surface to a short build window.

---

# ADR-0004: Promote ring detection and the gated auto-responder to core scope

**Status:** accepted · **Date:** 2026-08-26

**Context:** fraud-detection systems in this space are commonly framed as a "detector, verifier, or auto-responder," with "abuse-ring sentinel" as a well-known pattern. With a fixed, tighter timeline early on, both were reasonably scoped as a single optional stretch competing against a generalization check. With more time now committed to the build, that tradeoff no longer holds.

**Decision:** both ring detection and the gated auto-responder ship as core, alongside the entity-behavior detector and typology tagging. All three shapes, plus the named abuse-ring direction, from one engine.

**Consequences:** more surface area to get right in the available time, so the roadmap time-boxes each explicitly and the cut list demotes the console's ring viewer and the auto-responder before it ever touches the core detector or its evaluation. In exchange, this is now a meaningfully more complete project than a single-capability build would be.

**Alternatives considered:** keep the original stretch framing and spend the extra time on polish instead. Rejected because polish on a narrower scope is a weaker signal than genuine coverage of these directions.

---

# ADR-0005: Bring the frontend back into scope: a Risk Console over FastAPI + HTMX

**Status:** accepted · **Date:** 2026-08-26

**Context:** An earlier revision of this project explicitly cut the dashboard for time reasons (see the earlier "what's cut" language in the architecture doc). With more time available and a stated goal of a genuinely strong project, a way to make the engine's reasoning visible without reading a CSV became worth the build cost.

**Decision:** build a Risk Console, scoped to exactly five features (`06_FRONTEND_AND_DEMO.md`), using FastAPI and server-rendered HTMX templates. This reuses, rather than reopens, the original project's own ADR-0002 reasoning: one language, no build pipeline, no API-contract drift between a frontend and backend that would otherwise eat time better spent on the detection engine.

**Consequences:** real build time goes into the console, explicitly time-boxed (Roadmap, days 6 to 7) and explicitly bounded to five features so it doesn't become an open-ended product build. In exchange, measured precision and recall, honest false-positive cost, becomes something a reviewer can verify by looking at the metrics view, not just by trusting a claim in a README.

**Alternatives considered:** a React/TypeScript SPA, rejected for the same reason the original project rejected it: real skill, but the build-pipeline and state-management tax isn't worth it against the available time, and it doesn't make the underlying numbers any more true. A static, one-shot results export (images and tables, no live app) was also considered as a lower-cost alternative, but a live console supports the "flip between scored and demo" requirement (ADR-0006) in a way a static export can't.

---

# ADR-0006: Dual-mode demo layer, strictly separated from the scored evaluation

**Status:** accepted · **Date:** 2026-08-26

**Context:** the project's problem framing is grounded in Indian BFSI fraud specifically (PRD §2), but the project's primary dataset (IEEE-CIS) is global. Grounding the problem statement in real Indian fraud statistics addresses the narrative gap; it doesn't address the demo gap, showing the engine actually running against something shaped like a real Indian payment gateway's data.

**Decision:** add a synthetic Demo Adapter that produces transactions shaped like a real payment gateway payload (method, amount, entity-linkable fields), with a small injected ring for a reliable, demonstrable catch. Enforce separation from the scored evaluation at the schema level, a `source` field on every `Detection` (`benchmark` or `demo`), not just as a documentation convention someone has to remember to follow.

**Consequences:** the demo stream can never accidentally leak into a reported metric, since the field exists specifically to make that mistake visible immediately, in the console's own display, if it ever happened. In exchange, the project gets a platform-relevant, visually compelling demo without weakening the one claim that actually matters, the real, held-out, honestly-measured evaluation.

**Alternatives considered:** skip the demo layer entirely and rely on the India-context grounding alone. Considered sufficient for narrative honesty, but weaker for actually showing something running against the right shape of data, not just described in prose.

---

# ADR-0007: Orchestrator decides on population score + ring membership, not score_combined

**Status:** accepted · **Date:** 2026-10-07

**Context:** The original `Detection` contract (Architecture §4) and TDS-5 assumed the Orchestrator's primary confidence signal would be `score_combined` (population + entity-deviation together), written before any model had actually been run. Since then, a full, repeated investigation (`docs/LEARNING_LOG.md`, the Days 2-3 and post-deadline rebuild entries) established, with three independent lines of evidence and no remaining confounds, that entity-deviation does not improve PR-AUC over population-only for this detector, population-only consistently wins, including when restricted specifically to accounts with transaction history. Separately, ring detection (TDS-4) was independently validated as real signal, five credible clusters at 100% proxy fraud rate against a ~4.6% baseline.

**Decision:** the Orchestrator uses `score_population` (not `score_combined`) as its primary confidence input for the confidence gate, and treats ring membership (`ring_cluster_id` is set) as a second, independent, non-blended signal that can raise a detection's exposure to review/decline even when the population score alone wouldn't trigger it. `score_combined` and `score_entity_deviation` are still computed and stored on every `Detection` for transparency and the console's explain panel, just not used as the Orchestrator's decision driver. The typology tag rides along for human-readable explanation, not as a third scoring input.

**Consequences:** the system's actual decision logic now matches what was empirically proven to work, rather than what was assumed to work before any evidence existed. Makes the Orchestrator's reasoning more defensible (every input it acts on has its own validated evidence behind it), at the cost of diverging from the Detection contract's original implied design intent. `score_entity_deviation`/`score_combined` remain visible for honesty and future re-evaluation (e.g. if the entity fingerprint or feature set improves further), they're demoted, not deleted.

**Alternatives considered:**
- *Keep using `score_combined` as specified:* rejected, would mean knowingly building the auto-responder's core logic around a signal already shown to underperform, purely for spec-fidelity, not defensible once the evidence existed.
- *Blend ring membership into one combined score alongside population:* rejected for now, ring membership is a structurally different kind of evidence (graph connectivity, not a per-transaction feature), and keeping it as a separate, explicit gate is more explainable in the console later than burying it inside one opaque number.
