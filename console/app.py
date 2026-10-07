"""Risk Console (TDS-6).

Every route reads from the results store (results/) and renders. No
route computes a score, trains anything, or mutates pipeline state, a
console bug can't produce a wrong number, since it never produces one.
"""

import json
import math
from pathlib import Path

import jinja2
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

RESULTS = Path(__file__).resolve().parent.parent / "results"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

app = FastAPI(title="Sentinel Risk Console")

# Driving Jinja2 directly rather than starlette's Jinja2Templates wrapper:
# that wrapper hit a genuine internal error on this very-fresh package
# combo (Starlette 1.7.0 / FastAPI 0.142.2), see docs/LEARNING_LOG.md.
# Same templates, same inheritance/blocks, just no extra layer to fight.
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


def render(template_name: str, **context) -> HTMLResponse:
    template = jinja_env.get_template(template_name)
    return HTMLResponse(template.render(**context))


def load_detections() -> pd.DataFrame:
    return pd.read_csv(RESULTS / "detections.csv")


def to_records(df: pd.DataFrame) -> list[dict]:
    """.to_dict() alone leaves missing values as NaN, not None, and NaN
    is truthy in Python (bool(float('nan')) is True), so {% if %} in a
    template would get it wrong. Same root issue as Day 5's ring-member
    bug, fixed here before it becomes one, not after."""
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


@app.get("/", response_class=HTMLResponse)
def detection_feed():
    df = load_detections()
    flagged = df[df["decision"] != "allow"].sort_values("TransactionDT", ascending=False)
    return render(
        "feed.html",
        detections=to_records(flagged.head(200)),
        total=len(df),
        flagged_total=len(flagged),
    )


@app.get("/detection/{transaction_id}", response_class=HTMLResponse)
def explain_panel(transaction_id: str):
    df = load_detections()
    match = df[df["TransactionID"].astype(str) == transaction_id]
    if match.empty:
        raise HTTPException(404, "detection not found")
    return render("detection_partial.html", d=to_records(match)[0])


@app.get("/metrics", response_class=HTMLResponse)
def metrics_view():
    with open(RESULTS / "full_comparison.json") as f:
        comparison = json.load(f)
    baselines = to_records(pd.read_csv(RESULTS / "day1_baselines.csv"))
    return render(
        "metrics.html",
        comparison=sorted(comparison["results"], key=lambda r: r["pr_auc_full_test"], reverse=True),
        baselines=baselines,
        has_history_share=comparison["has_history_share"],
        history_diag=comparison.get("history_depth_diagnostic"),
    )


@app.get("/ring", response_class=HTMLResponse)
def ring_list():
    with open(RESULTS / "ring_clusters.json") as f:
        data = json.load(f)
    clusters = sorted(data["clusters"], key=lambda c: c["proxy_fraud_rate"], reverse=True)
    return render("ring_list.html", clusters=clusters)


@app.get("/ring/{cluster_id}", response_class=HTMLResponse)
def ring_viewer(cluster_id: str):
    with open(RESULTS / "ring_clusters.json") as f:
        data = json.load(f)
    cluster = next((c for c in data["clusters"] if c["cluster_id"] == cluster_id), None)
    if cluster is None:
        raise HTTPException(404, "ring cluster not found")

    devices = sorted({e["DeviceInfo"] for e in cluster["edges"]})
    node_ids = cluster["entities"] + devices
    cx, cy, r = 280, 280, 220
    positions = {
        node_id: (cx + r * math.cos(2 * math.pi * i / len(node_ids)), cy + r * math.sin(2 * math.pi * i / len(node_ids)))
        for i, node_id in enumerate(node_ids)
    }
    nodes = [
        {"id": node_id, "type": "entity" if node_id in cluster["entities"] else "device",
         "x": positions[node_id][0], "y": positions[node_id][1]}
        for node_id in node_ids
    ]
    edges = [
        {"x1": positions[e["entity_id"]][0], "y1": positions[e["entity_id"]][1],
         "x2": positions[e["DeviceInfo"]][0], "y2": positions[e["DeviceInfo"]][1]}
        for e in cluster["edges"]
    ]
    return render("ring.html", cluster=cluster, nodes=nodes, edges=edges)


@app.get("/audit", response_class=HTMLResponse)
def audit_trail(page: int = 1):
    df = pd.read_csv(RESULTS / "day5_audit_log.csv")
    page_size = 100
    start = (page - 1) * page_size
    page_df = df.iloc[start : start + page_size]
    total_pages = max(1, (len(df) + page_size - 1) // page_size)
    return render(
        "audit.html",
        records=to_records(page_df),
        page=page,
        total_pages=total_pages,
        total=len(df),
    )
