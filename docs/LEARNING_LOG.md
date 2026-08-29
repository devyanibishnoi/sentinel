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
