# Sentinel — Risk Console & Demo Layer

**Status:** Draft v1.0
**Owner:** Devyani Bishnoi

Companion to `02_ARCHITECTURE.md`. This doc exists because the console and the demo stream are substantial enough, and easy enough to scope-creep, that they need their own boundaries written down before building starts.

---

## 1. Purpose

The console has exactly one job: make the engine's rigor and reasoning visible in under a minute, for a reviewer who's never seen the codebase. It is not a product. It is not multi-tenant. It does not need accounts, settings, or anything beyond the five features below.

## 2. The five features, no more

1. **Detection feed** — a live-updating list of flagged transactions or demo events, newest first, showing entity id, combined score, timestamp, and source (`benchmark` or `demo`, visually distinct, never mixed in one unlabeled list).
2. **Explain panel** — click a detection, see a breakdown: population score, entity-deviation score, typology tag if any, ring cluster if any. This is the literal, clickable version of "explainable, bounded, gated." No detection is unexplained.
3. **Metrics view** — the results table from the Data & Eval spec, rendered: PR/ROC curves, baseline comparison, the entity-vs-population lift number, front and center, not buried in a CSV. This is where the track's own bar ("measured precision and recall on a held-out test set") becomes something a reviewer can verify by looking, not by trusting a claim.
4. **Ring viewer** — a simple force-directed or fixed-layout graph of one flagged cluster: nodes are entities, edges are shared fingerprints, sized by cluster proxy fraud rate. Doesn't need to be fancy, needs to make "this is a ring, not a coincidence" visually obvious in two seconds.
5. **Audit trail** — every auto-responder decision (allow/review/decline), with its reasoning, in one chronological list. Every refusal to act is in here too, not just the actions taken, matching the original project's "audit everything, including refusals" principle.

Nothing else. If a build session produces an idea for feature six, it goes in `05_ROADMAP.md`'s cut list, not into the console.

## 3. Tech

FastAPI + HTMX, server-rendered templates. No React, no build step, no client-side state management. The console reads from the results store and the audit log (Architecture §5) and renders; it does not compute anything itself. All computation happens in the backend pipeline, logged and reproducible independent of whether the console is even running.

## 4. The demo stream, precisely

The Demo Adapter (Architecture §3) generates transactions shaped like a real payment gateway payload: a payment method (card, UPI, netbanking, wallet), an amount in the smallest currency unit, a timestamp, and enough entity-linkable fields to support the same entity reconstruction logic used on the real dataset. Field names should be confirmed against Razorpay's actual API documentation once test-mode credentials are available, this doc describes the shape and intent, not a verified schema.

A small number of entities in the stream (roughly 5 to 10) deliberately share a device or card fingerprint at a rate that should trip the ring detector, so the ring viewer has something real to show on camera without waiting on a rare real-world case to surface in a random test-set slice.

**What the demo stream is never used for:** training, threshold selection, or any number that appears next to the words "precision," "recall," "FPR," or "PR-AUC." Its only job is to prove the pipeline runs against something shaped like the platform this project is built for. The video should say this explicitly, out loud, not leave it implied.

## 5. What "topnotch" means here, concretely

Not more features. These five, done so that:
- The explain panel answers "why" for every single row in the detection feed, no exceptions, no "score: 0.83" with nothing behind it.
- The metrics view is the thing a reviewer looks at first and can understand in ten seconds without narration.
- The ring viewer makes the abuse-ring story land without a paragraph of explanation.
- The audit trail makes "bounded and gated" a visible fact, not a claim in a README.
- The demo/benchmark separation is impossible to miss, not a footnote.

If those five hold up under a cold open, that's what "remarkable" looks like for this track. A sixth feature that dilutes any of the above is a worse use of time than polishing what's already in scope.
