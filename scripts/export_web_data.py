"""Exports curated, real result data into web/data/*.json for the
portfolio frontend (web/). Static data baked in at build time, no live
backend, Vercel just serves files. Every number here traces back to an
actual results/ file, nothing invented for the portfolio site.
"""

import json
from pathlib import Path

import pandas as pd

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

print("\ndone.")
