# Sentinel — Delivery Roadmap

**Status:** Draft v1.1
**Owner:** Devyani Bishnoi

---

## Pacing

Runway runs to the 5th. The plan below assumes a sustainable-but-intense pace, not a peak-output-every-single-day pace, since the careful judgment this project depends on (catching leakage, not overclaiming the demo, noticing what's actually broken) is exactly what degrades first under sleep debt. If a day goes faster than planned, pull forward from the next one. If a day goes slower, the cut list at the bottom exists so there's always a real, submittable thing regardless.

Two rules that hold no matter how the days actually land:
1. **Every session ends at a committable state.**
2. **The minimum deliverable must survive any cut:** IsolationForest with entity-deviation features beating the four baselines, honestly measured, on a held-out test set. Everything else, including the entire console, is built on top of that surviving first.

**Hard time-box: entity reconstruction and its sanity check get one day, day 1. If it's not holding up by the end of day 1, fall back and keep moving, per Architecture §7.**

---

## Day 1 — Scaffold, entities, baselines

- Stratified IEEE-CIS sample loaded, row counts and class balance printed.
- Proxy account reconstruction, sanity checks, inside the time-box.
- Population and entity-level baselines (all four from the Data & Eval spec), precision/recall/FPR printed.
- PRD's India-context problem statement finalized (already drafted, just needs the real numbers to survive a final read-through).

**Exit:** a number to beat, at both levels, written down.

## Days 2 to 3 — Real detector, the lift check

- IsolationForest on combined population + entity-deviation features.
- Held-out test evaluation at the entity-level split.
- The central number: does entity-deviation measurably beat population-only on PR-AUC. Report it either way.

**Exit:** this alone, if forced to stop here, is submittable against the track bar.

## Days 3 to 4 — Ring detection

- Shared-fingerprint graph, connected components.
- Cluster proxy fraud-rate evaluation, caveat attached everywhere it's shown.

**Exit:** at least one real cluster from the held-out set that the console's ring viewer will later be able to show.

## Day 5 — Gated auto-responder

- Playbook + Orchestrator (TDS-5), confidence and exposure gates.
- Full audit log, including refusals.

**Exit:** a decision trail that exists independent of the console, testable from the command line before any UI touches it.

## Days 6 to 7 — Risk Console

- FastAPI + HTMX, the five features from `06_FRONTEND_AND_DEMO.md`, no more.
- Detection feed and explain panel first (they're what every other feature hangs off of), metrics view and audit trail next, ring viewer last since it depends on day 3 to 4's output already existing.

**Exit:** a reviewer can open the console cold and understand the engine's reasoning without narration.

## Day 8 — Demo layer

- Demo Adapter, synthetic Razorpay-shaped stream, injected ring.
- Wired into the console with the `source` field making the benchmark/demo split visually unmissable.

**Exit:** the console can be flipped between "scored" and "demo" live, and it's obvious which is which at a glance.

## Day 9 — Polish, packaging, and the video

- README finalized with the results table and reproduction steps.
- Architecture diagram redrawn cleanly from `02_ARCHITECTURE.md`.
- 5-minute video: the entity-baseline idea in one sentence, the console live, the lift number, the ring catch, the auto-responder's audit trail, and whatever actually broke along the way.

## Buffer (if the 5th allows it)

- Autoencoder stretch model.
- Generalization check against the fallback dataset.
- A second pass at console polish.
- Sharpen the entity fingerprint: card1-6 + addr1/addr2 alone still lets some genuinely different real cards collide (largest observed cluster: 5,862 transactions, ~1% of the dataset, on one fully-specified combination). A day-count field (`D1`) combined with the transaction timestamp is a known approach for tightening this on IEEE-CIS specifically. Documented as a known limitation, not a blocker, per Architecture §7.

---

## Cut list, in order, if a day runs long

1. Buffer items first, obviously.
2. Ring viewer and demo layer (days 8 and the ring-viewer half of days 6 to 7), the console still works and is still explainable without them, just less visually complete.
3. Gated auto-responder (day 5), the detector and its evaluation stand on their own against the track bar without it.
4. Everything else in the console except the detection feed and explain panel, those two are the minimum needed to show the engine's reasoning at all.

The one thing that survives any cut, no matter how bad a week it is: the entity-baseline detector plus the lift number. That's the whole premise, and on its own, a complete answer to the track's bar.
