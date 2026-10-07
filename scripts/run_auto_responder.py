"""Day 5: Detection unification + typology tagging (TDS-3) + the gated
auto-responder (TDS-5, ADR-0007). Runs the Orchestrator over every test
transaction and writes a complete audit log, including every "allow".
"""

import sys
import time
from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.baselines import add_entity_prior_stats
from sentinel.entities import add_entity_id
from sentinel.features import FeaturePipeline
from sentinel.responder import Orchestrator, Playbook
from sentinel.rings import assign_cluster_ids, build_fingerprint_graph, find_clusters, score_cluster
from sentinel.splitting import add_split_column
from sentinel.typology import add_typology_tag

print("checkpoint: starting", flush=True)
transactions = pd.read_csv("data/raw/train_transaction.csv")
print("checkpoint: loaded transactions", flush=True)
transactions = add_entity_id(transactions)
print("checkpoint: added entity_id", flush=True)
transactions = add_split_column(transactions)
print("checkpoint: added split", flush=True)
transactions = add_entity_prior_stats(transactions)
print("checkpoint: added entity prior stats", flush=True)

identity = pd.read_csv("data/raw/train_identity.csv")[["TransactionID", "DeviceInfo"]]
transactions = transactions.merge(identity, on="TransactionID", how="left")
print("checkpoint: merged identity", flush=True)

train = transactions[transactions["split"] == "train"]
val = transactions[transactions["split"] == "val"]
test = transactions[transactions["split"] == "test"].copy()

# ---- 1. Scores: score_population drives the gate (ADR-0007). score_combined
# and score_entity_deviation are kept for transparency, not used to decide. ----
pipeline = FeaturePipeline().fit(train)
print("checkpoint: fitted feature pipeline", flush=True)

X_train_pop = pipeline.transform(train, include_entity=False)
print(f"checkpoint: built X_train_pop, shape={X_train_pop.shape}", flush=True)
pop_model = IsolationForest(n_estimators=200, contamination="auto", random_state=42, n_jobs=-1).fit(X_train_pop)
print("checkpoint: fitted pop_model", flush=True)
val_score_population = -pop_model.score_samples(pipeline.transform(val, include_entity=False))
test["score_population"] = -pop_model.score_samples(pipeline.transform(test, include_entity=False))
print("checkpoint: scored val/test with pop_model", flush=True)

X_train_combined = pipeline.transform(train, include_entity=True)
combined_model = IsolationForest(n_estimators=200, contamination="auto", random_state=42, n_jobs=-1).fit(X_train_combined)
print("checkpoint: fitted combined_model", flush=True)
test["score_combined"] = -combined_model.score_samples(pipeline.transform(test, include_entity=True))
test["score_entity_deviation"] = test["score_combined"] - test["score_population"]
print("checkpoint: scored test with combined_model", flush=True)

# ---- 2. Ring membership: a cluster only counts as a trigger if it is BOTH
# statistically credible (5+ transactions, not a 2-sample coincidence) AND
# actually elevated above baseline (size alone says nothing about whether
# it's suspicious, a big cluster at ordinary fraud rate is just a popular
# device, not a ring). ----
overall_fraud_rate = float(test["isFraud"].mean())
RING_MIN_TRANSACTIONS = 5
RING_MIN_FRAUD_RATE_MULTIPLE = 3.0

graph = build_fingerprint_graph(test, fingerprint_col="DeviceInfo", min_entities_per_fingerprint=2, max_entities_per_fingerprint=20)
all_clusters = find_clusters(graph, min_size=2, max_size=50)
scored_clusters = [score_cluster(c, test) | {"entities": c} for c in all_clusters]
credible_clusters = [
    c["entities"]
    for c in scored_clusters
    if c["n_transactions"] >= RING_MIN_TRANSACTIONS
    and c["proxy_fraud_rate"] >= overall_fraud_rate * RING_MIN_FRAUD_RATE_MULTIPLE
]
print(f"clusters passing size filter only (5+ txns): "
      f"{sum(1 for c in scored_clusters if c['n_transactions'] >= RING_MIN_TRANSACTIONS)}")
print(f"clusters passing BOTH size and fraud-rate-elevation filter "
      f"(>= {RING_MIN_FRAUD_RATE_MULTIPLE}x baseline): {len(credible_clusters)}")

entity_to_cluster = assign_cluster_ids(credible_clusters)
test["ring_cluster_id"] = test["entity_id"].map(entity_to_cluster)
# Not fixing this with .where(..., None): pandas 3.0's string dtype can't
# hold a literal None anyway (see sentinel/responder.py), the Orchestrator
# checks isinstance(..., str) instead of an identity check, which works
# regardless of what the missing marker actually is.

# ---- 3. Typology tag, explanation only, not a gate input. ----
test = add_typology_tag(test)

# ---- 4. Thresholds, chosen on VAL/TRAIN, never on test. ----
confidence_threshold = float(pd.Series(val_score_population).quantile(0.98))
exposure_threshold = float(train["TransactionAmt"].quantile(0.75))
print(f"confidence_threshold (98th pct of val population score): {confidence_threshold:.4f}")
print(f"exposure_threshold (75th pct of train TransactionAmt): {exposure_threshold:.2f}")
print(f"credible ring clusters feeding the gate: {len(credible_clusters)}")
print()

# ---- 5. Run the Orchestrator over EVERY test row. ----
playbook = Playbook(confidence_threshold=confidence_threshold, exposure_threshold=exposure_threshold)
orchestrator = Orchestrator(playbook)

start = time.time()
orchestrator_columns = [
    "TransactionID", "entity_id", "score_population", "ring_cluster_id", "typology_tag", "TransactionAmt",
]
audit_records = []
for detection in test[orchestrator_columns].to_dict(orient="records"):
    decision = orchestrator.evaluate(detection)
    record = orchestrator.audit(detection, decision)
    audit_records.append(record)
elapsed = time.time() - start
print(f"evaluated {len(audit_records)} detections in {elapsed:.1f}s")

audit_df = pd.DataFrame([r.__dict__ for r in audit_records])
assert len(audit_df) == len(test), "every test row must produce exactly one audit record, no exceptions"

print()
print("decision counts:")
print(audit_df["decision"].value_counts())
print()
print("one example reasoning per decision type:")
for action in ["decline", "review", "allow"]:
    example = audit_df[audit_df["decision"] == action].head(1)
    if len(example):
        print(f"  {action}: {example['reasoning'].iloc[0]}")

Path("results").mkdir(exist_ok=True)
audit_df.to_csv("results/day5_audit_log.csv", index=False)
print("\nsaved to results/day5_audit_log.csv")
