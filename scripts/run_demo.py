"""Day 8: the demo layer (TDS-1b). Generates a synthetic, payment-
gateway-shaped stream with an injected ring, scores it with the
ALREADY-TRAINED model (loaded, never re-fit), and runs it through the
same ring detection / typology / Orchestrator pipeline as the real
benchmark, tagged source="demo" throughout.

Ring credibility here uses find_credible_rings_live (sentinel.rings),
not find_credible_rings: this stream has no ground truth, a live system
never knows a brand-new cluster's true fraud rate the moment it spots
it, so credibility is judged by two independent unsupervised signals
agreeing (graph structure + population anomaly score), not by fraud
rate elevation.
"""

import json
import sys
import time
from pathlib import Path

import joblib
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.baselines import add_entity_prior_stats
from sentinel.demo import generate_demo_transactions
from sentinel.entities import add_entity_id
from sentinel.responder import Orchestrator, Playbook
from sentinel.rings import assign_cluster_ids, build_fingerprint_graph, find_clusters, find_credible_rings_live
from sentinel.typology import add_typology_tag

print("checkpoint: starting", flush=True)

# Only need train to bootstrap realistic feature distributions for the
# synthetic stream, never fit on it here.
real_transactions = pd.read_csv("data/raw/train_transaction.csv", nrows=200_000)
demo = generate_demo_transactions(real_transactions, n_entities=60, ring_size=7)
print(f"checkpoint: generated {len(demo)} demo transactions", flush=True)

demo = add_entity_id(demo)
demo = add_entity_prior_stats(demo)
print(f"checkpoint: added entity_id + prior stats, {demo['entity_id'].nunique()} demo entities", flush=True)

pipeline = joblib.load("models/feature_pipeline.joblib")
pop_model = joblib.load("models/pop_model.joblib")
combined_model = joblib.load("models/combined_model.joblib")
thresholds = joblib.load("models/playbook_thresholds.joblib")
print("checkpoint: loaded persisted pipeline, models, thresholds", flush=True)

demo["score_population"] = -pop_model.score_samples(pipeline.transform(demo, include_entity=False))
demo["score_combined"] = -combined_model.score_samples(pipeline.transform(demo, include_entity=True))
demo["score_entity_deviation"] = demo["score_combined"] - demo["score_population"]
print("checkpoint: scored demo stream (no fitting happened on this data)", flush=True)

# ---- Ring detection, live-safe credibility (no ground truth available). ----
graph = build_fingerprint_graph(demo, fingerprint_col="DeviceInfo", min_entities_per_fingerprint=2, max_entities_per_fingerprint=20)
all_clusters = find_clusters(graph, min_size=2, max_size=50)
credible = find_credible_rings_live(all_clusters, demo)
print(f"demo clusters found: {len(all_clusters)}   credible (live-safe rule): {len(credible)}")

entity_to_cluster = assign_cluster_ids([c["entities"] for c in credible])
demo["ring_cluster_id"] = demo["entity_id"].map(entity_to_cluster)

demo = add_typology_tag(demo)

# ---- Orchestrator: same playbook, same code, different data. ----
playbook = Playbook(confidence_threshold=thresholds["confidence_threshold"], exposure_threshold=thresholds["exposure_threshold"])
orchestrator = Orchestrator(playbook)

start = time.time()
orchestrator_columns = ["TransactionID", "entity_id", "score_population", "ring_cluster_id", "typology_tag", "TransactionAmt"]
audit_records = []
for detection in demo[orchestrator_columns].to_dict(orient="records"):
    decision = orchestrator.evaluate(detection)
    record = orchestrator.audit(detection, decision)
    audit_records.append(record)
print(f"evaluated {len(audit_records)} demo detections in {time.time() - start:.1f}s")

audit_df = pd.DataFrame([r.__dict__ for r in audit_records])
assert len(audit_df) == len(demo), "every demo row must produce exactly one audit record too, no exceptions"

print()
print("demo decision counts:")
print(audit_df["decision"].value_counts())

injected_ring_rows = demo[demo["demo_injected_ring"]]
caught = injected_ring_rows["ring_cluster_id"].notna().sum()
print(f"\ninjected ring: {len(injected_ring_rows)} rows, {caught} correctly tagged with a ring_cluster_id")

Path("results").mkdir(exist_ok=True)
audit_df.to_csv("results/demo_audit_log.csv", index=False)

demo_detections = demo[
    ["TransactionID", "entity_id", "TransactionDT", "TransactionAmt",
     "score_population", "score_entity_deviation", "score_combined",
     "typology_tag", "ring_cluster_id", "isFraud"]
].copy()
demo_detections["TransactionID"] = demo_detections["TransactionID"].astype(str)
demo_detections = demo_detections.merge(
    audit_df.rename(columns={"transaction_id": "TransactionID"})[["TransactionID", "decision", "reasoning"]],
    on="TransactionID",
    how="left",
)
demo_detections["source"] = "demo"
demo_detections = demo_detections.rename(columns={"isFraud": "ground_truth_fraud", "reasoning": "decision_reasoning"})
demo_detections.to_csv("results/demo_detections.csv", index=False)

# Ring viewer data for the demo stream, same shape as the benchmark one.
demo_ring_clusters = []
for i, c in enumerate(credible):
    label = f"demo_ring_{i}"
    entities = c["entities"]
    cluster_rows = demo[demo["entity_id"].isin(entities) & demo["DeviceInfo"].notna()]
    edges = cluster_rows[["entity_id", "DeviceInfo"]].drop_duplicates().to_dict(orient="records")
    demo_ring_clusters.append({
        "cluster_id": label,
        "entities": sorted(entities),
        "n_entities": c["n_entities"],
        "n_transactions": c["n_transactions"],
        "proxy_fraud_rate": None,  # explicit, not just absent: demo has no ground truth at all
        "avg_population_score": c["avg_population_score"],
        "edges": edges,
    })
with open("results/demo_ring_clusters.json", "w") as f:
    json.dump({
        "caveat": "demo stream has no ground truth; credibility here is judged by population-score agreement, not fraud-rate elevation",
        "clusters": demo_ring_clusters,
    }, f, indent=2)

print(f"\nsaved results/demo_audit_log.csv, results/demo_detections.csv, results/demo_ring_clusters.json ({len(demo_ring_clusters)} rings)")
