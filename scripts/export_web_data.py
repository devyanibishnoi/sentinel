"""Exports curated, real result data into web/data/*.json for the
portfolio frontend (web/). Static data baked in at build time, no live
backend, Vercel just serves files. Every number here traces back to an
actual results/ file, nothing invented for the portfolio site.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

RESULTS = Path("results")
OUT = Path("web/data")
OUT.mkdir(parents=True, exist_ok=True)


def write(name: str, obj) -> None:
    with open(OUT / name, "w") as f:
        json.dump(obj, f, indent=2, default=str)
    print(f"wrote web/data/{name}")


# ---- Comparison (the central lift check) ----
with open(RESULTS / "full_comparison.json") as f:
    comparison = json.load(f)
write("comparison.json", comparison)

# ---- Baselines ----
baselines = pd.read_csv(RESULTS / "day1_baselines.csv").to_dict(orient="records")
write("baselines.json", baselines)

# ---- Benchmark detections: all flagged + a sample of allows, for a
# representative, demonstrable, not-85k-rows dataset. ----
detections = pd.read_csv(RESULTS / "detections.csv", dtype={"TransactionID": str})
flagged = detections[detections["decision"] != "allow"]
allowed_sample = detections[detections["decision"] == "allow"].sample(n=300, random_state=42)
curated = pd.concat([flagged, allowed_sample]).sort_values("TransactionDT", ascending=False)
curated = curated.astype(object).where(pd.notna(curated), None)
write("detections.json", curated.to_dict(orient="records"))
print(f"  ({len(flagged)} flagged + {len(allowed_sample)} sampled allows = {len(curated)} total)")

# ---- Ring clusters: top 20 by fraud rate, WITH edges for the graph view. ----
with open(RESULTS / "ring_clusters.json") as f:
    ring_data = json.load(f)
top_rings = sorted(ring_data["clusters"], key=lambda c: c["proxy_fraud_rate"], reverse=True)[:20]
write("rings.json", {"caveat": ring_data["caveat"], "clusters": top_rings})

# ---- Demo stream: small enough to include whole. ----
demo_detections = pd.read_csv(RESULTS / "demo_detections.csv", dtype={"TransactionID": str})
demo_detections = demo_detections.astype(object).where(pd.notna(demo_detections), None)
write("demo_detections.json", demo_detections.to_dict(orient="records"))

with open(RESULTS / "demo_ring_clusters.json") as f:
    demo_ring_data = json.load(f)
write("demo_rings.json", demo_ring_data)

# ---- Threshold explorer: precision/recall/FPR as a function of the
# population-score confidence threshold, computed from the REAL full
# 85,004-row held-out test set (not the curated excerpt above), so the
# interactive numbers match the reported PR-AUC exactly. This sweeps
# ONLY the confidence/score threshold; the real Orchestrator also
# triggers independently on ring membership and separately gates
# decline-vs-review by exposure (TransactionAmt), neither of which this
# curve reproduces, the web page says so next to the chart. ----
full = pd.read_csv(RESULTS / "detections.csv")
y_true = full["ground_truth_fraud"].astype(int).to_numpy()
y_score = full["score_population"].to_numpy()

precision, recall, thresholds = precision_recall_curve(y_true, y_score)
precision, recall = precision[:-1], recall[:-1]  # drop the trailing (1, 0, inf) point

n_points = 250
if len(thresholds) > n_points:
    idx = np.linspace(0, len(thresholds) - 1, n_points).astype(int)
    thresholds, precision, recall = thresholds[idx], precision[idx], recall[idx]

n_total = len(y_true)
n_negative = int(n_total - y_true.sum())
curve = []
for t, p, r in zip(thresholds, precision, recall):
    flagged = y_score >= t
    n_flagged = int(flagged.sum())
    n_tp = int((flagged & (y_true == 1)).sum())
    fpr = (n_flagged - n_tp) / n_negative if n_negative else 0.0
    curve.append({
        "threshold": float(t),
        "precision": float(p),
        "recall": float(r),
        "fpr": float(fpr),
        "n_flagged": n_flagged,
    })

playbook_thresholds = joblib.load("models/playbook_thresholds.joblib")
write(
    "threshold_curve.json",
    {
        "curve": curve,
        "n_total": n_total,
        "n_fraud": int(y_true.sum()),
        "deployed_confidence_threshold": float(playbook_thresholds["confidence_threshold"]),
    },
)

print("\ndone.")
