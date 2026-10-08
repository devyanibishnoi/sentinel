"""Fit the feature pipeline and both IsolationForest models ONCE on the
real benchmark train split, and persist them. Any script scoring new
data (demo included) loads these, it never re-fits, that's what "the
demo stream never contributes to a reported metric, only scores with
the already-trained model" actually means in practice, not just
"same random seed happens to reproduce it."
"""

import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.baselines import add_entity_prior_stats
from sentinel.entities import add_entity_id
from sentinel.features import FeaturePipeline
from sentinel.splitting import add_split_column

print("checkpoint: starting", flush=True)
transactions = pd.read_csv("data/raw/train_transaction.csv")
transactions = add_entity_id(transactions)
transactions = add_split_column(transactions)
transactions = add_entity_prior_stats(transactions)
print("checkpoint: entity_id, split, prior stats done", flush=True)

train = transactions[transactions["split"] == "train"]
val = transactions[transactions["split"] == "val"]

pipeline = FeaturePipeline().fit(train)
print("checkpoint: fitted feature pipeline", flush=True)

X_train_pop = pipeline.transform(train, include_entity=False)
pop_model = IsolationForest(n_estimators=200, contamination="auto", random_state=42, n_jobs=-1).fit(X_train_pop)
print("checkpoint: fitted pop_model", flush=True)

X_train_combined = pipeline.transform(train, include_entity=True)
combined_model = IsolationForest(n_estimators=200, contamination="auto", random_state=42, n_jobs=-1).fit(X_train_combined)
print("checkpoint: fitted combined_model", flush=True)

# Orchestrator thresholds (ADR-0007), calibrated once here on val/train so
# every script that scores new data (benchmark test, demo) uses the exact
# same numbers, loaded, never recomputed and hoped to match.
val_score_population = -pop_model.score_samples(pipeline.transform(val, include_entity=False))
confidence_threshold = float(pd.Series(val_score_population).quantile(0.98))
exposure_threshold = float(train["TransactionAmt"].quantile(0.75))
print(f"checkpoint: confidence_threshold={confidence_threshold:.4f}  exposure_threshold={exposure_threshold:.2f}", flush=True)

Path("models").mkdir(exist_ok=True)
joblib.dump(pipeline, "models/feature_pipeline.joblib")
joblib.dump(pop_model, "models/pop_model.joblib")
joblib.dump(combined_model, "models/combined_model.joblib")
joblib.dump(
    {"confidence_threshold": confidence_threshold, "exposure_threshold": exposure_threshold},
    "models/playbook_thresholds.joblib",
)
print("saved pipeline, both models, and playbook thresholds to models/")
