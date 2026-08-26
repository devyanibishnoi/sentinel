# Sentinel — Technical Design Specifications

One section per component. Read alongside `02_ARCHITECTURE.md` (the `Detection` contract), `03_DATA_AND_EVALUATION.md`, and `06_FRONTEND_AND_DEMO.md` (the console).

---

## TDS-1 — Ingestion & Entity Reconstruction

**Responsibility:** turn raw transaction data into normalized feature vectors keyed by a proxy entity, leak-free.

**Interface:**
```python
class DatasetAdapter(Protocol):
    def load(self, path: str) -> Iterator[RawTransaction]: ...
    def normalize(self, raw: RawTransaction) -> Event: ...
    def reconstruct_entity_id(self, raw: RawTransaction) -> str: ...
    def dataset_hash(self) -> str: ...

class FeaturePipeline:
    def fit(self, events: Iterable[Event]) -> None: ...
    def transform(self, events: Iterable[Event]) -> FeatureMatrix: ...
```

**Core logic:** entity reconstruction runs once at load, immediately followed by the sanity check from the Data & Eval spec.

**Open questions:** which field combination is most stable, needs empirical validation.

---

## TDS-1b — Demo Adapter

**Responsibility:** generate synthetic, Razorpay-shaped transactions for the console demo, implementing the same `DatasetAdapter` interface as TDS-1 so the rest of the pipeline treats it identically.

**Interface:** same `DatasetAdapter` protocol as TDS-1, plus:
```python
class DemoAdapter(DatasetAdapter):
    def inject_ring(self, n_entities: int, shared_fingerprint: str) -> None: ...
```

**Core logic:** produces `Event` objects tagged `source="demo"` at normalization time (Architecture §4), so the separation from scored results is enforced in the data itself, not left to application logic to remember. Never used to fit anything, only to score with the already-trained model.

**Open questions:** exact field names should mirror Razorpay's real API once test-mode credentials confirm the schema; this spec describes shape, not a verified contract.

---

## TDS-2 — Detection Engine

**Responsibility:** score each transaction against both the population and its own entity's history.

**Interface:**
```python
class Scorer(Protocol):
    def fit(self, X: FeatureMatrix) -> None: ...
    def score(self, X: FeatureMatrix) -> np.ndarray: ...

class EntityBaseline:
    def fit(self, events: Iterable[Event], entity_key: str) -> None: ...
    def deviation(self, event: Event) -> float: ...

class DetectionEngine:
    def __init__(self, population_scorer: Scorer, entity_baseline: EntityBaseline, threshold: float): ...
    def run(self, events, features) -> Iterator[Detection]: ...
```

**Core logic:** combined score as a function of population and entity-deviation scores. Cold-start entities get an explicit tag, not a fabricated baseline.

**Open questions:** how many prior transactions before an entity's baseline is trusted.

---

## TDS-3 — Typology Tagging

**Responsibility:** attach descriptive, unscored tags to flagged transactions.

**Interface:**
```python
class TypologyTagger:
    def tag(self, d: Detection, evidence: dict) -> str | None: ...
```

**Core logic:** rule-based (device mismatch, amount deviation, cold start). Not scored, no ground-truth subtypes exist.

---

## TDS-4 — Ring Detection

**Responsibility:** flag clusters of entities sharing device or card fingerprints at a suspicious rate.

**Interface:**
```python
class RingDetector:
    def build_graph(self, events: Iterable[Event]) -> Graph: ...
    def find_clusters(self, graph: Graph, min_size: int) -> list[Cluster]: ...
    def score_cluster(self, cluster: Cluster, labels) -> float: ...
```

**Core logic:** `networkx` connected components. Cluster proxy fraud rate reported with the ground-truth caveat every time.

**Open questions:** edge weight/threshold to avoid merging unrelated entities via one popular shared fingerprint (a common connected-components failure mode).

---

## TDS-5 — Gated Auto-Responder

**Responsibility:** turn a high-confidence Detection into a decision, with a complete audit trail.

**Interface:**
```python
class Playbook:
    trigger: TriggerCondition          # score/typology/ring match
    confidence_threshold: float
    exposure_threshold: float          # transaction amount as the exposure proxy

class Orchestrator:
    def evaluate(self, d: Detection) -> Decision: ...   # allow | review | decline
    def audit(self, d: Detection, decision: Decision, reasoning: str) -> AuditRecord: ...
```

**Core logic:** on a Detection, check confidence against `confidence_threshold` and exposure against `exposure_threshold`. Above confidence and below exposure, act autonomously (decline or allow per the specific rule that matched). Above exposure or below confidence, route to review rather than guess. Every call to `evaluate`, including ones that route to review, produces an `AuditRecord`, there is no code path that makes a decision without one.

**Open questions:** whether `exposure_threshold` should scale with the entity's own typical transaction size rather than being a flat cutoff, worth testing empirically once real score distributions exist.

---

## TDS-6 — Risk Console

**Responsibility:** render the detection feed, explain panel, metrics view, ring viewer, and audit trail. Full feature boundary in `06_FRONTEND_AND_DEMO.md`.

**Interface:**
```python
# FastAPI routes, server-rendered HTMX partials, no client-side state
GET  /                    # detection feed
GET  /detection/{id}      # explain panel (HTMX partial)
GET  /metrics             # metrics view
GET  /ring/{cluster_id}   # ring viewer
GET  /audit                # audit trail
```

**Core logic:** every route reads from the results store or audit log and renders; no route computes a score, trains anything, or mutates pipeline state. This keeps the console fully decoupled from correctness, a console bug can't produce a wrong number, since it never produces numbers, only displays ones already logged.
