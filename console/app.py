"""Risk Console (TDS-6).

Every route reads from the results store (results/) and renders. No
route computes a score, trains anything, or mutates pipeline state, a
console bug can't produce a wrong number, since it never produces one.

Benchmark vs demo (Day 8, Architecture §4): the detection feed and
audit trail can be flipped between the two via a `source` query param.
Metrics is ALWAYS benchmark-only, never a toggle, the demo stream must
never contribute to a reported metric, full stop.
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


def to_records(df: pd.DataFrame) -> list[dict]:
    """.to_dict() alone leaves missing values as NaN, not None, and NaN
    is truthy in Python (bool(float('nan')) is True), so {% if %} in a
    template would get it wrong. Same root issue as Day 5's ring-member
    bug, fixed here before it becomes one, not after."""
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


def detections_file(source: str) -> Path:
    if source not in ("benchmark", "demo"):
        raise HTTPException(400, "source must be 'benchmark' or 'demo'")
    return RESULTS / ("detections.csv" if source == "benchmark" else "demo_detections.csv")


def audit_file(source: str) -> Path:
    if source not in ("benchmark", "demo"):
        raise HTTPException(400, "source must be 'benchmark' or 'demo'")
    return RESULTS / ("day5_audit_log.csv" if source == "benchmark" else "demo_audit_log.csv")


@app.get("/", response_class=HTMLResponse)
def detection_feed(source: str = "benchmark"):
    df = pd.read_csv(detections_file(source))
    if source == "benchmark":
        # 85k rows: show only what was actually flagged.
        shown = df[df["decision"] != "allow"].sort_values("TransactionDT", ascending=False)
    else:
        # demo stream is small and illustrative: show everything, flagged or not.
        shown = df.sort_values("TransactionDT", ascending=False)
    return render(
        "feed.html",
        detections=to_records(shown.head(200)),
        total=len(df),
        flagged_total=len(df[df["decision"] != "allow"]),
        source=source,
    )


@app.get("/detection/{transaction_id}", response_class=HTMLResponse)
def explain_panel(transaction_id: str, source: str = "benchmark"):
    df = pd.read_csv(detections_file(source))
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


def _load_all_ring_clusters() -> list[dict]:
    clusters = []
    for name, source in [("ring_clusters.json", "benchmark"), ("demo_ring_clusters.json", "demo")]:
        path = RESULTS / name
        if not path.exists():
            continue
        with open(path) as f:
            data = json.load(f)
        for c in data["clusters"]:
            c = dict(c)
            c["source"] = source
            clusters.append(c)
    return clusters


@app.get("/ring", response_class=HTMLResponse)
def ring_list():
    clusters = _load_all_ring_clusters()
    clusters.sort(key=lambda c: c.get("proxy_fraud_rate") or c.get("avg_population_score") or 0, reverse=True)
    return render("ring_list.html", clusters=clusters)


@app.get("/ring/{cluster_id}", response_class=HTMLResponse)
def ring_viewer(cluster_id: str):
    cluster = next((c for c in _load_all_ring_clusters() if c["cluster_id"] == cluster_id), None)
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
def audit_trail(page: int = 1, source: str = "benchmark"):
    df = pd.read_csv(audit_file(source))
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
        source=source,
    )
