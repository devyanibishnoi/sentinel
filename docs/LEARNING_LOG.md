# Sentinel — Learning Log

This is the running notebook for the project. Every time a new concept comes up while building, the explanation gets logged here, in order, so by the end this reads like a small book of everything learned building Sentinel.

Format: one dated entry per teaching moment, with a short heading for the concept.

---

*Voice and format rules for this file live in `CLAUDE.md` at the repo root, first person, informal, technically real, what broke and how it got fixed.*

---

## Day 1, OneDrive locked my own file mid-move

setting up `data/raw/` for the IEEE-CIS CSVs, a plain `mv` on `train_transaction.csv` (683MB) kept failing with "Device or resource busy," right after unzipping it. no program had it open as far as I could tell, which is the confusing part.

turned out both my Downloads folder and the project folder live under OneDrive's Desktop backup, so OneDrive was actively hashing/uploading the file the second it hit disk, and that upload holds a lock a plain rename can't push past.

fix: copy instead of move, then verify the copy's byte size matches the original exactly before touching the source, only delete the original once that check passes. copy worked because reading a file that's locked-for-write is usually fine even when renaming it isn't. the delete on the original still failed (still locked), so there's a harmless duplicate sitting in Downloads for now, wasted space, not a project bug.

not a fraud-detection lesson, but a real one: "device busy" on a plain filesystem op almost always means some background process (sync client, antivirus, indexer) has a handle on the file, not that anything is actually broken. verify-then-delete instead of trusting a move blindly is just how I'm doing this from here on.

## Day 1, pandas 3.0 broke my "astype(str) means it's definitely a string now" assumption

building `entity_id` by gluing 8 card/address columns together with `.astype(str)` then `.join()`. seemed obviously fine, that's the whole point of `astype(str)`. blew up instead: `TypeError: sequence item 1: expected str instance, float found`.

confusing part: I checked the dtype after the cast and it said `str`. so why is `join()` finding an actual float inside a column that claims to be string dtype now? turns out I'm on pandas 3.0.5, a genuinely new major version, and it changed how missing values behave under `astype(str)`. older pandas used to turn a blank cell into the literal text `"nan"` when cast to string. pandas 3.0's string dtype doesn't silently do that anymore, a missing value stays missing (still a raw float underneath) instead of getting stringified into fake text. that's arguably the right call, "nan" showing up as a real string value was always a classic footgun, but it broke the assumption I didn't know I was making.

fix: `fillna("missing")` before `astype(str)`, so what happens to a missing value is a decision I made on purpose, not an accident. bonus: it made the next problem visible instead of hidden, see the entity-cluster sanity check below.

## Day 1, the entity fingerprint isn't clean, and that's informative, not a failure

ran the sanity check on `entity_id` (card1-6 + addr1/addr2 glued together): 590,540 transactions collapse into 43,071 unique entities. median transactions-per-entity is 2, which feels right for "mostly individual cards." but the biggest cluster is 9,900 transactions, 1.7% of the entire dataset, claiming to be "one account."

looked at what the biggest clusters actually have in common and found two different failure modes hiding in the same number:
1. some huge clusters have `addr1`/`addr2` both missing, meaning "no address on file" is itself acting like a shared fingerprint, gluing together transactions that have nothing to do with each other. that's the bug I expected going in.
2. some huge clusters have a *real*, fully-specified address, and are still enormous (5,862 transactions on one combination). that one I didn't expect: it means card1-6 + addr1/addr2 alone just isn't a fine-grained enough fingerprint on its own, plenty of genuinely different cards from the same bank/network/region look identical on these 8 fields.

this is exactly the thing ADR-0002 warned about upfront ("not verified ground truth," "sanity-check before anything downstream trusts it"), it's satisfying to actually hit the real version of the warning instead of just nodding at it in a doc. the fix isn't "throw the approach out," it's "don't let missing data merge unrelated rows" (treat missing-address rows as their own entity, not one shared bucket) and, if there's time later, sharpen the fingerprint further with more fields (people on Kaggle have used a day-count column called D1 for this same dataset for exactly this reason). for now, given the one-day time-box on this step, fixing failure mode 1 and documenting failure mode 2 as a known limitation is the right amount of effort, not chasing a perfect entity ID.

## Day 1, an entity-level split means the entity baseline can't use train history at all

almost built this wrong. entity-level baselines are supposed to compare a transaction to "this account's own past." but an entity-level train/test split means an entity is *entirely* in one split, never both, so a test-split entity has zero rows in train. if I'd built "entity's historical max" from train data, that rule would just never fire for any test entity, because none of them exist there.

realized this before writing the bug, not after, by actually thinking through what the split guarantees instead of assuming. fix: the entity baseline has to be built from that same entity's own strictly-earlier transactions, computed fresh within whichever split it lives in, sorted by time, never touching train for this part. `entity_prior_count`, `entity_prior_max`, `entity_prior_mean`, `entity_prior_std`: all `groupby(entity_id)` + `cummax()/expanding()` + `.shift(1)`, the shift is what keeps a transaction from ever seeing its own value (or the future) in its own baseline.

direct consequence: an entity's first-ever transaction has nothing to compare against, that's a cold start (TDS-2), no fabricated baseline, just excluded from that specific evaluation. turned out to be 18.5-22.4% of the test split, given how the entity fingerprint (see above) makes most entities tiny.

## Day 1, naive entity rules did not obviously beat population rules, and that's the honest result

ran all five mandatory baselines on the held-out test split. random baseline landed almost exactly on the true fraud rate (3.4% precision/recall/FPR, all ~equal), which is the correct sanity check, that's what randomly flagging at the true base rate is supposed to produce, and it means the split/eval pipeline is wired right.

the part I didn't expect: rule_entity (flag if this is a new record-high amount for this specific account) came out at 3.3% precision, technically *below* random. statistical_entity did a bit better (3.8%) but still didn't blow population-level rules out of the water.

not a bug, and not hiding it: a single hand-written per-entity rule just isn't enough evidence on its own for the "entity-deviation beats population" thesis. that's the whole reason the real detector (IsolationForest, combining several population and entity-deviation features together, next) exists, instead of shipping one clever rule. baselines are supposed to be beatable, that's the point of building them first.

## Days 2-3, the central number came back negative, and finding out why was the actual work

this is the number the entire project stands on: does entity-deviation measurably beat population-only on PR-AUC. fit IsolationForest twice on identical train data, once on population features only (amount, time-of-day, card/address fields, Vesta's C1-C14), once on population + our entity-deviation features (prior count, z-score vs this entity's own history, ratio to this entity's own prior max). scored both against the held-out test set.

population-only: PR-AUC 0.0922. combined: PR-AUC 0.0910. lift: **-0.0012**. negative. the roadmap says report it either way, so: it's a no.

didn't stop there, because a flat "no" isn't an explanation, it's just a number. formed a real hypothesis: this morning's entity-fingerprint problem (some "entities" are actually thousands of different real cards colliding on the same 8-field key, see the reconstruction entry above) could be poisoning the entity-deviation features, since a fake mega-entity's "personal history" is actually a population statistic wearing a disguise. checked it: 31.2% of test rows sit inside an entity with 100+ prior transactions, and the single biggest one is 5,766 rows. plausible-sounding story.

tested it anyway instead of just asserting it, restricted evaluation to entities with prior_count <= 20 (i.e. entities small enough to plausibly be real individual accounts) and re-measured. lift got *more* negative (-0.0026), not less. hypothesis rejected by my own data. good that I checked, would've written up a confident explanation that was just wrong.

tried a second angle: TDS-2 actually specifies combining population and entity scores as two separate scorers merged at the end, not one shared feature table for a single model, which is what I'd built. tested three late-fusion combinations (max, mean, weighted average of rank-normalized scores). all three came back considerably *worse* than the joint-feature version (-0.026 to -0.05 vs -0.0012). so it wasn't a fusion-method artifact either, both real architectures tried, neither shows a lift.

the actual answer showed up when I checked fraud rate by cold-start status instead of guessing further: fraud rate on entities' first-ever transaction (no prior history, feature defaults to neutral by design, TDS-2's no-fabricated-baseline rule) is **7.8%**. fraud rate on transactions where an entity *does* have history is **2.4%**. and **42% of all fraud in the test set happens on a cold-start transaction**. an entity-deviation feature is structurally blind to that 42%, by definition, there's nothing to deviate from yet. this isn't a bug in the feature, it's what "no history" has to mean.

the part that actually clicked for me: I'd already included a `entity_has_history` binary flag in the combined feature set, so in theory the model had access to exactly this correlation. it didn't matter, because IsolationForest is unsupervised, it never sees `isFraud` during fitting, so it has no mechanism to learn "this flag correlates with the label," it only reacts to structural isolability in the feature space itself. a feature can be a perfect predictor and an unsupervised isolation-based model still won't necessarily use it that way, correlation with an unseen label isn't the same thing as being easy to isolate.

this is also, retroactively, why TDS-3 puts "cold start" in the typology tagger as an explicit, named, rule-based tag instead of leaving it for a black-box score to maybe discover. I read that design decision in the spec before writing a line of code and didn't really feel it, now I have the number that makes it obviously the right call: cold-start deserves to be said out loud, not buried inside a feature an unsupervised model has no reason to weight correctly.

**honest Day 2-3 conclusion:** entity-deviation as currently built does not improve PR-AUC over population-only, under either fusion strategy tested, and the reason is identifiable and specific (cold-start concentration of fraud, invisible to an unsupervised model by construction), not a mystery or a bug. reported as-is, per the "no dropped negative results" rule. this is still a complete, defensible answer on its own, an honestly-measured negative result from a properly built evaluation is worth more than an inflated positive one.

## Days 3-4, the same bug from Day 1 came back one layer deeper

ring detection: entities are nodes, draw an edge between two entities if they share a `DeviceInfo` fingerprint, connected components = candidate rings. TDS-4 itself names the risk up front: "avoid merging unrelated entities via one popular shared fingerprint." recognized this immediately, it's literally this morning's missing-address bug wearing a different outfit, so I checked the real distribution before picking a threshold instead of guessing. good call: `Windows` alone spans 5,410 distinct entities in the test split, `iOS Device` 1,456, obviously not device fingerprints in any meaningful sense. capped it to fingerprints shared by 2-20 entities, which naturally excluded every generic string without me hand-writing a blocklist.

thought that was the whole fix. it wasn't. the largest resulting cluster was still 442 entities, 42,164 transactions, and its proxy fraud rate (2.6%) was *below* the overall baseline (3.4%). a real ring should look more fraud-heavy than average, not less, so that number itself was the tell that something was still wrong.

turned out capping how popular a *single* fingerprint value can be doesn't stop connected components from chaining through *many different, individually-small* fingerprints: entity A and B share device X (15 entities, passes the cap fine), B and C share a completely unrelated device Y (18 entities, also passes), and so on, each individual link looks innocent, but the transitive chain balloons into something huge anyway. same underlying failure mode as the address-collision bug, missing/generic values acting as false connective tissue, just operating through indirect chains this time instead of one direct shared value. connected components will happily walk through as many hops as exist, and nothing about capping edge popularity stops that.

fix: cap the final *component size* too (max 50 entities), not just the fingerprint popularity going into it, and treat any component that blows past that as probably shared infrastructure noise rather than a ring, which the below-baseline fraud rate directly supports.

after that fix: 437 real clusters left, and restricting to ones with 5+ transactions (avoiding the small-sample-noise problem, a handful of clusters showed "100% fraud" on just 2-3 transactions, which isn't strong evidence of anything), the strongest cluster is **15 entities, 15 transactions, 100% fraud rate**, against a 3.4% baseline. that's genuinely exciting, and it's the first clearly positive result of the whole build so far, after the honest negative from the lift check.

worth naming the pattern explicitly since it's now shown up twice in one build: any technique that groups things by "shared attribute" needs a check for both (a) is any single shared value too generic, and (b) can indirect chaining through many individually-fine values still produce something huge anyway. capping (a) alone isn't enough, checked that the hard way, twice now.

## Coming back after missing the original deadline: two real upgrades, now that there's actual time

missed the original internal deadline for this project. not treating that as the end of it, treating it as permission to go back and actually fix the two things that were deliberately deferred under time pressure, instead of rushing straight to the console.

**fix 1, the entity fingerprint:** added a reverse-engineered trick the Kaggle community uses on this exact dataset: `D1` behaves like "days since this card was first seen," and `TransactionDT / 86400` also increases with real time at the same rate, so `(TransactionDT / 86400) - D1` cancels the time-passing part out and leaves roughly a constant per real account, "which day it first showed up." Added that to the fingerprint alongside card/address fields. Result: biggest fake-looking cluster dropped from 5,862 transactions down to 1,414, a real, measurable improvement, not perfect (1,414 is still too big to be one real account), but a legitimate step forward, and `D1` itself is only missing on 0.2% of rows, so it's a reliable field to lean on. Documenting the residual imperfection rather than claiming this is now solved, chasing it to zero would be diminishing returns against a problem that's structurally unsolvable with proxy data anyway.

**fix 2, the split:** switched from a random entity split to a time-based one, entities ordered by their earliest transaction, train gets the earliest-appearing ones, test gets the latest. This is a more honest simulation of real deployment, you train on the past and get evaluated on genuinely new accounts you've never seen, not on a random sample from the same time period as training.

this immediately surfaced something the random split had been hiding: fraud rate is 3.0% in train but 4.6-4.9% in val/test. fraud rate drifts upward over time in this dataset. a random split spreads that drift evenly across train/test and never lets you notice it happened. this is the real reason time-based splits are considered the more rigorous choice for anything with a time dimension, not just a style preference, they stop you from accidentally training and evaluating on a mixture that doesn't reflect how the data actually arrives in the real world.

## Re-running the baselines with both fixes: cold-start share basically tripled, and that's good news in disguise

re-ran the four baselines with the sharpened fingerprint + time-based split. the headline number: cold-start share (test transactions with zero prior history for their entity) jumped from 18.5-22.4% before to **64.7-79.1%** now.

first reaction was "did I break something." didn't. the OLD fingerprint was blunter, which meant it was accidentally manufacturing fake "history" for a lot of entities by falsely merging unrelated transactions together, the exact Day 1 collision bug. with that mostly fixed, what we're seeing now is much closer to the TRUE rate of genuinely-first-ever transactions. it was always this high, the old numbers were just wrong in a way that happened to look more comfortable.

this strengthens, not undermines, the earlier finding that cold start explains the flat IsolationForest lift. if anything there's even less of the dataset where an entity-deviation signal could possibly apply than originally estimated. good to know before rebuilding the central experiment, not after.

side finding worth sitting with, not concluding anything from yet: within the now-smaller, now-more-accurate has-history subset, the entity rules catch noticeably more fraud proportionally (recall roughly doubled) but also throw far more false alarms (FPR up to ~19-21%). makes sense directionally, a cleaner history signal should be more informative when it exists, but noisier because that remaining subset is now much smaller and each individual score matters more. revisiting this properly once the IsolationForest comparison is rebuilt.

## The rebuilt central experiment: entity-deviation still doesn't lift, and now we know exactly why, with no confounds left

rebuilt the whole comparison with the sharpened fingerprint + time-based split, and also built the thing we said we'd build: one shared metric (PR-AUC) across every baseline AND both IsolationForest variants, on the SAME test set, reported both on the full test set and restricted to has-history rows only.

good news first: IsolationForest now clearly, convincingly beats every single baseline, ~3x the PR-AUC of the best baseline (0.166 vs 0.055). that's the "compare against all four baselines" requirement actually satisfied properly, not just gestured at across differently-shaped reports.

the harder news: entity-deviation still doesn't lift. population-only (0.1656) beats combined (0.1557) on the full test set, AND population-only still wins restricted to has-history rows only (0.0639 vs 0.0620), which is the exact check built specifically to rule out the cold-start explanation. cold start isn't the excuse anymore, we controlled for it directly, and the answer is still no.

so I went looking for the next-level explanation instead of stopping at "still negative." checked the actual depth of history among has-history rows: median is 2 prior transactions, and 41% of has-history rows have exactly 1 prior transaction, which means no standard deviation exists yet (can't compute variance from one point), so the z-score feature defaults to neutral for those too. the entity signal is starved twice over: 64.7% of the test set has zero history at all, and a large chunk of the remaining 35.3% barely has enough history to compute anything meaningful from. only a genuinely small slice of the test set has both (a) any history and (b) enough of it to produce a real statistic.

this is a complete, honestly-earned answer now, not a guess: entity-deviation (built this specific way, amount-based z-score and ratio-to-prior-max) doesn't help on this dataset because most individual account histories in this time window are simply too thin to baseline against, not because of a fingerprint bug (fixed), not because of a bad split (fixed), not because cold-start was hiding the signal (controlled for directly). three independent lines of evidence (cold-start fraud concentration, the corrected higher cold-start rate, and now history-depth sparsity) all point the same way. that's what a properly investigated negative result looks like, and it's a stronger, more defensible thing to put in front of a judge than a lucky positive number would have been.

## Ring detection improved too, as a direct side effect of the fingerprint fix

re-ran ring detection with the sharpened `entity_id`, no changes to the ring-detection logic itself, same `DeviceInfo` fingerprint, same 2-20 entity cap, same 50-entity component cap. results improved anyway: zero oversized/noise components this time (there was 1 before), and instead of one credible cluster, there are now **five separate clusters, all at 100% fraud rate** (5 to 12 entities each), against a 4.6% baseline.

worth naming why this happened even though I didn't touch the ring code: a cleaner `entity_id` means the graph's nodes (the entities) are themselves more accurate, so a shared-device connection between two "entities" is now much more likely to represent an actual shared device between two actual different people, rather than between two fingerprint-collision artifacts. fixing a problem upstream (entity reconstruction) paid off downstream (ring detection) for free, which is a decent argument for fixing root causes instead of patching symptoms at each individual component.

## Day 5, the spec assumed something our own evidence already disproved, so I changed it instead of pretending not to notice

started building the gated auto-responder (TDS-5) and hit a real conflict immediately: the original `Detection` contract and TDS-5 assume the Orchestrator's main confidence signal is `score_combined`, population + entity-deviation together. that assumption was written before any model had actually run. we now have a thoroughly investigated, three-ways-confirmed result that entity-deviation does NOT improve on population-only for this detector, population-only wins every time we checked, including the has-history-only check built specifically to be fair to the entity signal.

building the auto-responder around `score_combined` anyway, just because that's what the spec originally said, would mean knowingly wiring the system's actual decisions through a signal already shown not to work. that's spec-fidelity for its own sake, not good engineering, so I didn't do it. wrote it up as ADR-0007 instead of quietly deciding alone: Orchestrator uses `score_population` as the real confidence input, and treats ring membership (which DID hold up, five clusters at 100% proxy fraud) as a separate, independent trigger rather than blending it into one number. `score_combined` still gets computed and stored on every Detection, for transparency and so the console can show it later, it's demoted, not deleted, in case a better entity fingerprint or feature set someday changes the answer.

the actual lesson: a spec written before evidence exists is a hypothesis, not a commitment. the point of all the investigation work wasn't to produce a number for a report, it was to actually let the number change what gets built next. updating TDS-5 and the ADR log to match reality is what "the docs are the live source of truth" is supposed to mean in practice, not just a thing that's true until it's inconvenient.

## Day 5, first real run: zero allows out of 85,004, and three separate things were actually wrong

first full run of the auto-responder came back with every single test transaction declined or reviewed, zero allows, against a 4.57% real fraud rate. obviously broken. took three real fixes to actually get it right, in order.

**bug 1, size isn't suspicion.** I filtered ring clusters as "credible" by transaction count alone (5+), but never checked whether the cluster's fraud rate was actually elevated. 251 clusters passed that filter, most of them probably just ordinary groups of people who happen to share a not-quite-generic-enough device, not rings. fix: also require the proxy fraud rate to be at least 3x the baseline. that cut it down to 70 real candidates.

**bug 2, the exact Day 1 pandas gotcha came back a third time, in a new costume.** fixed the ring membership check by writing `None` into a column for non-members, using `.where(ring_map.notna(), None)`. ran it: still zero allows. traced an actual row and found the "fix" produced `nan`, as a `float`, not `None`. pandas 3.0's string dtype has its own internal missing-value marker, and both `None` and `NaN` get normalized into that SAME marker the moment they land in a string-dtype column, there's no way to make it hold literal Python `None`. same root mechanism as the Day 1 `astype(str)` bug (pandas 3.0 changed what "missing" means inside its own string dtype), just surfacing through a completely different operation this time. real fix: stop checking identity against a value whose "missing" representation I can't control, check `isinstance(value, str)` instead, a real cluster id is always a string, anything else isn't, regardless of which specific sentinel pandas chose to use for "absent."

**bug 3, not a logic bug at all, a resource one.** even after both fixes, the script kept getting silently killed with zero output, five times in a row. turned out `test.to_dict(orient="records")` was converting the WHOLE test dataframe, ~400 columns across 85,004 rows, into a list of Python dicts, when the Orchestrator only needed 6 of those columns. selecting just the needed columns first (`test[orchestrator_columns].to_dict(...)`) dropped the per-row evaluation from part of a multi-minute hang down to 0.6 seconds.

**a fourth thing, not a bug in the code, a lesson about this environment:** every time I issued a NEW terminal command to check on the stuck process, the background run appears to have been killed as a side effect, even though nothing about my script caused that. once I stopped interrupting it and just waited, it finished cleanly in reasonable time. worth remembering: when a background process is genuinely still working, poking at it to check on it can be the thing that kills it, patience is sometimes the actual fix, not another diagnostic command.

## Days 6-7, the Risk Console, and one more very-fresh-package surprise

built the console: FastAPI + Jinja2 + HTMX, five routes (detection feed, explain panel, metrics, ring viewer, audit trail), all reading from a new results store (`results/detections.csv`, `results/ring_clusters.json`) instead of computing anything themselves, per TDS-6.

before building it, went back and fixed a real inconsistency: the standalone ring-detection script was only checking cluster SIZE as "credible," not fraud-rate elevation, the exact bug Day 5 caught in the auto-responder. pulled that logic into one shared function (`sentinel.rings.find_credible_rings`) so there's one definition of "credible ring" used everywhere, not two scripts quietly disagreeing with each other. upstream fix, downstream consistency, again.

first attempt at wiring up the routes crashed deep inside Jinja2's template cache: `TypeError: cannot use 'tuple' as a dict key (unhashable type: 'dict')`, nothing in my own code, a genuine internal error inside starlette's `Jinja2Templates` wrapper on this install (Starlette 1.7.0, FastAPI 0.142.2, both versions far newer than anything I'd expect to have seen documented anywhere). didn't spend time reverse-engineering someone else's internals, same philosophy as the pandas 3.0 surprises: when a well-known operation breaks in a brand-new library version, the fast path is often routing around the broken layer, not debugging it. drove Jinja2 directly (`jinja2.Environment` + `FileSystemLoader`) instead of the wrapper, same templates, same inheritance, same output, just one fewer unfamiliar layer between my code and the one that actually renders HTML.

applied the Day 5 NaN-vs-None lesson proactively this time instead of waiting to hit it again: wrote a `to_records()` helper that explicitly converts missing values to real `None` before anything reaches a template, since `bool(float('nan'))` is `True` in Python, a template's `{% if %}` would have treated a missing typology tag as "present" otherwise. caught it by remembering the exact shape of the earlier bug, not by hitting it live this time, that's what logging these things is actually for.

verified all five routes two ways: FastAPI's `TestClient` (in-process, no server, no ports) for a fast first check, then an actual running server loaded in a real browser, clicking through the HTMX explain panel and the ring viewer live, per this project's own rule that UI changes get checked in a browser, not just asserted to work.

## Day 8, the demo layer, and a reasoned design choice that was empirically wrong

built the demo stream: synthetic transactions bootstrapped from real train-data feature distributions (fresh IDs/timestamps, never a copy of one real person's record), with a small deliberately-planted ring, several entities sharing one obviously-synthetic device string. this is scored by the ALREADY-TRAINED model, loaded from disk via `joblib` (persisted once in a new `scripts/fit_pipeline.py`, not re-fit here), which is what "never retrains on the demo stream" actually means in practice, not just "happens to reproduce the same model via a fixed random seed."

before writing any of this, worked out a real problem: the benchmark's "credible ring" rule (size AND fraud-rate elevation) can't run on live/demo data at all, there's no ground truth to check fraud-rate elevation against, a live system never knows a brand-new cluster's true fraud rate the moment it spots it. reasoned through a fix: swap "is the fraud rate elevated" for "are this cluster's members ALSO independently flagged as anomalous by the population model," two unsupervised signals agreeing, available without labels.

ran it. the deliberately-planted test ring got caught by the graph, then silently filtered back OUT by my own new rule, zero rings survived. good, legible failure, and worth sitting with instead of just loosening a number. the ring's transactions were bootstrapped from genuinely ordinary real rows, so individually they don't look anomalous to the population model at all. my rule was requiring something that the planted ring, by design, didn't have.

the actual bug was in the reasoning, not the code: requiring population-score agreement was solving a problem the SIZE and PER-FINGERPRINT-POPULARITY caps already solve (those are what stop the two known false-positive modes, a too-generic shared value and connected-component chaining). what it was ACTUALLY doing was screening out rings built from normal-looking transactions, which is the realistic, evasive kind of ring a real operation would construct specifically to dodge amount-based detection, not a case to exclude.

fix: drop the score as a filter, keep it as attached, displayed corroborating evidence instead, a human reviewing a flagged cluster can see "73% of this cluster also scores high individually" as extra context, without the system silently discarding a structurally-real cluster for not also clearing a second, unrelated bar. re-ran: 13 of 13 planted-ring transactions correctly caught.

the honest, remaining limitation, worth stating plainly rather than hiding: live ring detection, without labels, necessarily has lower precision than the offline-validated 3x-baseline rule we proved out on the benchmark. that's not a bug to fix, it's the real, inherent cost of not having ground truth at decision time, and it's exactly why the Orchestrator still gates ring-triggered actions on exposure (decline only within a safe amount, review above it) rather than treating "it's in a cluster" alone as proof.

one more small thing worth explaining rather than ignoring: the console showed the planted ring as 10 linked accounts, not the 7 I set `ring_size=7` to. traced it instead of shrugging: 4 of the 7 synthetic donor templates happened to have a missing card field, so each of THEIR transactions became its own `unmatched_` entity (the exact same Day 1 behavior, correctly firing on synthetic data), and one entity's transactions happened to straddle a simulated day boundary without me advancing its `D1` field to match, splitting it into two proxy identities. both are the same entity-reconstruction logic, already trusted on real data, doing exactly what it's supposed to, just on synthetic input this time. net result: still a fully correct catch, all 10 fragments genuinely do share the planted device, just more dramatic than planned. not treating this as a bug to fix, it's real behavior from already-validated code, not an error in new code.
