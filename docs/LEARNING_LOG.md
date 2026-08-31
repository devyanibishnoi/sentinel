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

**honest Day 2-3 conclusion:** entity-deviation as currently built does not improve PR-AUC over population-only, under either fusion strategy tested, and the reason is identifiable and specific (cold-start concentration of fraud, invisible to an unsupervised model by construction), not a mystery or a bug. reported as-is, per the "no dropped negative results" rule. this is still a complete, submittable answer to the track's bar, an honestly-measured negative result from a properly built evaluation is worth more than an inflated positive one.

## Days 3-4, the same bug from Day 1 came back one layer deeper

ring detection: entities are nodes, draw an edge between two entities if they share a `DeviceInfo` fingerprint, connected components = candidate rings. TDS-4 itself names the risk up front: "avoid merging unrelated entities via one popular shared fingerprint." recognized this immediately, it's literally this morning's missing-address bug wearing a different outfit, so I checked the real distribution before picking a threshold instead of guessing. good call: `Windows` alone spans 5,410 distinct entities in the test split, `iOS Device` 1,456, obviously not device fingerprints in any meaningful sense. capped it to fingerprints shared by 2-20 entities, which naturally excluded every generic string without me hand-writing a blocklist.

thought that was the whole fix. it wasn't. the largest resulting cluster was still 442 entities, 42,164 transactions, and its proxy fraud rate (2.6%) was *below* the overall baseline (3.4%). a real ring should look more fraud-heavy than average, not less, so that number itself was the tell that something was still wrong.

turned out capping how popular a *single* fingerprint value can be doesn't stop connected components from chaining through *many different, individually-small* fingerprints: entity A and B share device X (15 entities, passes the cap fine), B and C share a completely unrelated device Y (18 entities, also passes), and so on, each individual link looks innocent, but the transitive chain balloons into something huge anyway. same underlying failure mode as the address-collision bug, missing/generic values acting as false connective tissue, just operating through indirect chains this time instead of one direct shared value. connected components will happily walk through as many hops as exist, and nothing about capping edge popularity stops that.

fix: cap the final *component size* too (max 50 entities), not just the fingerprint popularity going into it, and treat any component that blows past that as probably shared infrastructure noise rather than a ring, which the below-baseline fraud rate directly supports.

after that fix: 437 real clusters left, and restricting to ones with 5+ transactions (avoiding the small-sample-noise problem, a handful of clusters showed "100% fraud" on just 2-3 transactions, which isn't strong evidence of anything), the strongest cluster is **15 entities, 15 transactions, 100% fraud rate**, against a 3.4% baseline. that's genuinely exciting, and it's the first clearly positive result of the whole build so far, after the honest negative from the lift check.

worth naming the pattern explicitly since it's now shown up twice in one build: any technique that groups things by "shared attribute" needs a check for both (a) is any single shared value too generic, and (b) can indirect chaining through many individually-fine values still produce something huge anyway. capping (a) alone isn't enough, checked that the hard way, twice now.
