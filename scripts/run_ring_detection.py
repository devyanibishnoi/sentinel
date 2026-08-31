"""Days 3-4 exit criterion: at least one real cluster from the held-out
test split, with a proxy fraud rate (caveated, not ground truth).
"""

import json
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.entities import add_entity_id
from sentinel.rings import build_fingerprint_graph, find_clusters, score_cluster
from sentinel.splitting import add_split_column

transactions = pd.read_csv("data/raw/train_transaction.csv")
transactions = add_entity_id(transactions)
transactions = add_split_column(transactions)

identity = pd.read_csv("data/raw/train_identity.csv")[["TransactionID", "DeviceInfo"]]
transactions = transactions.merge(identity, on="TransactionID", how="left")

test = transactions[transactions["split"] == "test"]

graph = build_fingerprint_graph(
    test,
    fingerprint_col="DeviceInfo",
    min_entities_per_fingerprint=2,
    max_entities_per_fingerprint=20,
)
all_components = list(nx.connected_components(graph))
clusters = find_clusters(graph, min_size=2, max_size=50)
n_oversized = sum(
    1 for c in all_components if len({n for n in c if "::" not in n}) > 50
)

print(f"graph nodes: {graph.number_of_nodes()}   edges: {graph.number_of_edges()}")
print(f"clusters found (2-50 entities): {len(clusters)}")
print(f"oversized components excluded (>50 entities, likely infrastructure noise, not a ring): {n_oversized}")
print()

scored = [score_cluster(c, test) for c in clusters]
scored.sort(key=lambda c: c["proxy_fraud_rate"], reverse=True)

overall_fraud_rate = float(test["isFraud"].mean())
print(f"reference: overall test-split fraud rate = {overall_fraud_rate:.4f}")
print("CAVEAT: every proxy_fraud_rate below is a DERIVED PROXY, not verified ground truth.")
print()

print("top 10 clusters by proxy fraud rate (includes small-sample results, read with caution):")
for c in scored[:10]:
    print(
        f"  entities={c['n_entities']:3d}  transactions={c['n_transactions']:4d}  "
        f"proxy_fraud_rate={c['proxy_fraud_rate']:.4f}  fraud_txns={c['n_fraud_transactions']}"
    )

print()
credible = [c for c in scored if c["n_transactions"] >= 5]
print(f"top 5 clusters by proxy fraud rate, restricted to n_transactions >= 5 (more statistically credible):")
for c in credible[:5]:
    print(
        f"  entities={c['n_entities']:3d}  transactions={c['n_transactions']:4d}  "
        f"proxy_fraud_rate={c['proxy_fraud_rate']:.4f}  fraud_txns={c['n_fraud_transactions']}"
    )

Path("results").mkdir(exist_ok=True)
with open("results/day3_4_ring_detection.json", "w") as f:
    json.dump(
        {
            "caveat": "proxy_fraud_rate is a DERIVED PROXY LABEL, not verified ground truth, everywhere it appears in this file",
            "fingerprint_field": "DeviceInfo",
            "min_entities_per_fingerprint": 2,
            "max_entities_per_fingerprint": 20,
            "overall_test_fraud_rate": overall_fraud_rate,
            "max_size": 50,
            "n_oversized_components_excluded": n_oversized,
            "n_clusters_found": len(clusters),
            "clusters": scored,
        },
        f,
        indent=2,
    )
print("\nsaved to results/day3_4_ring_detection.json")
