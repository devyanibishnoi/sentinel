# Architecture Decision Records

ADRs capture *why* a decision was made, the alternatives, and the tradeoffs, so future-you (or a reviewer) doesn't have to reverse-engineer intent.

---

## Template

```
# ADR-NNNN — <title>
Status: proposed | accepted | superseded by ADR-XXXX
Date: YYYY-MM-DD
Context: what forces are at play?
Decision: what we're doing.
Consequences: what this makes easy, what it makes hard, what we're accepting.
Alternatives considered: and why not.
```

---

# ADR-0001 — Class of loss: account-level behavioral fraud, not isolated transaction scoring

**Status:** accepted · **Date:** 2026-08-26

**Context:** Track 02 (AI Risk Manager) lists several valid directions: chargeback evidence, return-risk scoring, fraud-spike detection, abuse-ring detection. A flat "is this transaction fraud" classifier can satisfy the track's bar on paper, but it throws away the most defensible signal available: whether a transaction is normal for the specific account it belongs to.

**Decision:** build the detector around per-entity behavioral baselines (UEBA: User and Entity Behavior Analytics), not just population-level anomaly scoring. Every transaction gets scored twice: how unusual is this in general, and how unusual is this for this specific account. Abuse-ring detection is treated as a direct extension of the same entity model (shared fingerprints across accounts) rather than a separate system, covering two of the track's four example directions from one engine.

**Consequences:** requires a dataset with a real or reconstructable entity identifier, which rules out simpler anonymized transaction datasets and adds real preprocessing work. In exchange, produces a detector that catches account-takeover-style fraud a population-only model misses entirely, and gives a genuinely defensible answer to why this looks like security work applied to a fintech problem, not just a fraud classifier with a new coat of paint.

**Alternatives considered:**
- *Flat population-level classifier* — simpler, faster to build, satisfies the track's bar on paper, but has no answer for why it's a distinctive approach versus any other fraud model, and can't extend cleanly into ring detection.
- *Chargeback-evidence or return-risk as the primary loss type* — both valid track directions, but neither has the same natural entity-behavior framing, and public dataset support for them is weaker.

---

# ADR-0002 — Entity reconstruction and dataset choice: IEEE-CIS over an anonymized transaction set

**Status:** accepted · **Date:** 2026-08-26

**Context:** Per-entity baselining (ADR-0001) requires knowing which transactions belong to the same account. Fully anonymized, PCA-transformed transaction datasets have no such identifier at all.

**Decision:** use IEEE-CIS Fraud Detection as the primary dataset, and reconstruct a proxy account identity by combining stable card and address fields. Validate this reconstruction with an explicit sanity check (transactions-per-entity distribution, no absurdly large clusters) before anything downstream depends on it. A simpler, anonymized dataset (ULB Credit Card Fraud) is kept as a named fallback with a coarser, session-level entity proxy if the reconstruction doesn't hold up.

**Consequences:** meaningfully more preprocessing risk and effort than an anonymized single-file dataset would require. Proxy identity reconstruction is a known but approximate technique, not verified ground truth, and this is documented everywhere it matters rather than glossed over. In exchange, this is the only path that actually supports the project's core premise; without it, the entity-behavior story has nothing to baseline against.

**Alternatives considered:**
- *ULB Credit Card Fraud as primary* — clean, fast, no preprocessing burden, but has no entity identifier at all, so per-entity baselining isn't possible. Demoted to fallback status.
- *Synthetic account-behavior generator* — avoids the proxy-identity risk entirely, but loses the "real, defensible, held-out test set" framing the track explicitly asks for. Kept as a fallback-of-the-fallback if IEEE-CIS proves unworkable in the available time.

---

# ADR-0003 — Core stack and scope cuts for the build window

**Status:** accepted · **Date:** 2026-08-26

**Context:** The full space of what a mature fraud-risk platform could include (dashboard, LLM-based enrichment, gated response automation, live feeds) is much larger than what a time-boxed build window supports.

**Decision:** Python core (scikit-learn, pandas), no dashboard, no LLM/RAG enrichment layer, no SOAR-style response infrastructure, no live data feeds. `networkx` is the one addition, for the ring-detection stretch goal, chosen for being lightweight with no new infra required. Results are reported via a script or notebook and a markdown results table, not a deployed service.

**Consequences:** keeps the entire time budget on the detection engine and its evaluation, which is where the actual signal (and the actual track bar) lives. Accepts that the deliverable won't look like a finished product, which is fine: the buildathon's own stated criteria is a repo that runs, a short video, and an honest account of what broke, not a polished UI.

**Alternatives considered:**
- *A minimal dashboard* — would help demo the results visually, but a clean results table and a walked-through notebook cover the same need for a 5-minute video without the build cost. Not pursued.
- *LLM-based typology enrichment* — tempting given prior RAG experience, but the descriptive rule-based typology tagger (TDS-3) already satisfies the "explain the flag in plain language" need without adding a new dependency and a new failure surface to a short build window.

---

# ADR-0004 — Promote ring detection and the gated auto-responder to core scope

**Status:** accepted · **Date:** 2026-08-26

**Context:** Track 02's bar allows a "detector, verifier, or auto-responder," and lists "abuse-ring sentinel" as a named example direction. With a fixed, tighter timeline, both were reasonably scoped as a single optional stretch competing against a generalization check. With more time now committed to the build, that tradeoff no longer holds.

**Decision:** both ring detection and the gated auto-responder ship as core, alongside the entity-behavior detector and typology tagging. All three of the track's allowed shapes, plus the named abuse-ring direction, from one engine.

**Consequences:** more surface area to get right in the available time, so the roadmap time-boxes each explicitly and the cut list demotes the console's ring viewer and the auto-responder before it ever touches the core detector or its evaluation. In exchange, this is now a meaningfully more complete answer to the track than a single-capability submission would be.

**Alternatives considered:** keep the original stretch framing and spend the extra time on polish instead. Rejected because polish on a narrower scope is a weaker signal than genuine coverage of the track's own named directions.

---

# ADR-0005 — Bring the frontend back into scope: a Risk Console over FastAPI + HTMX

**Status:** accepted · **Date:** 2026-08-26

**Context:** An earlier revision of this project explicitly cut the dashboard for time reasons (see the earlier "what's cut" language in the architecture doc). With more time available and a stated goal of a genuinely strong submission, a way to make the engine's reasoning visible without reading a CSV became worth the build cost.

**Decision:** build a Risk Console, scoped to exactly five features (`06_FRONTEND_AND_DEMO.md`), using FastAPI and server-rendered HTMX templates. This reuses, rather than reopens, the original project's own ADR-0002 reasoning: one language, no build pipeline, no API-contract drift between a frontend and backend that would otherwise eat time better spent on the detection engine.

**Consequences:** real build time goes into the console, explicitly time-boxed (Roadmap, days 6 to 7) and explicitly bounded to five features so it doesn't become an open-ended product build. In exchange, the track's bar, measured precision and recall, honest false-positive cost, becomes something a reviewer can verify by looking at the metrics view, not just by trusting a claim in a README.

**Alternatives considered:** a React/TypeScript SPA, rejected for the same reason the original project rejected it: real skill, but the build-pipeline and state-management tax isn't worth it against the available time, and it doesn't make the underlying numbers any more true. A static, one-shot results export (images and tables, no live app) was also considered as a lower-cost alternative, but a live console supports the "flip between scored and demo" requirement (ADR-0006) in a way a static export can't.

---

# ADR-0006 — Dual-mode demo layer, strictly separated from the scored evaluation

**Status:** accepted · **Date:** 2026-08-26

**Context:** The track's "why now" names Indian BFSI specifically, but the project's primary dataset (IEEE-CIS) is global. Grounding the problem statement in real Indian fraud statistics (ADR context, see PRD §2) addresses the narrative gap; it doesn't address the demo gap, showing the engine actually running against something shaped like a real Indian payment gateway's data.

**Decision:** add a synthetic Demo Adapter that produces transactions shaped like a real payment gateway payload (method, amount, entity-linkable fields), with a small injected ring for a reliable on-camera catch. Enforce separation from the scored evaluation at the schema level, a `source` field on every `Detection` (`benchmark` or `demo`), not just as a documentation convention someone has to remember to follow.

**Consequences:** the demo stream can never accidentally leak into a reported metric, since the field exists specifically to make that mistake visible immediately, in the console's own display, if it ever happened. In exchange, the submission gets a platform-relevant, visually compelling demo without weakening the one claim that actually matters for the track's bar, the real, held-out, honestly-measured evaluation.

**Alternatives considered:** skip the demo layer entirely and rely on the India-context grounding alone. Considered sufficient for narrative honesty, but weaker for a 5-minute video that benefits from something visibly running against the right shape of data, not just described in prose.
