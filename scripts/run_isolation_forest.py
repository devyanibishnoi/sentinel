"""Days 2-3 exit criterion: does entity-deviation measurably beat
population-only on PR-AUC? The one number the whole project stands on.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.baselines import add_entity_prior_stats
from sentinel.entities import add_entity_id
from sentinel.features import FeaturePipeline
from sentinel.splitting import add_split_column

transactions = pd.read_csv("data/raw/train_transaction.csv")
transactions = add_entity_id(transactions)
transactions = add_split_column(transactions)
transactions = add_entity_prior_stats(transactions)

train = transactions[transactions["split"] == "train"]
test = transactions[transactions["split"] == "test"]
y_test = test["isFraud"].to_numpy()

pipeline = FeaturePipeline().fit(train)


def run(include_entity: bool, name: str) -> dict:
    X_train = pipeline.transform(train, include_entity=include_entity)
    X_test = pipeline.transform(test, include_entity=include_entity)

    model = IsolationForest(n_estimators=200, contamination="auto", random_state=42, n_jobs=-1)
    model.fit(X_train)

    # score_samples: higher = more normal. Flip sign so higher = more anomalous,
    # matching the convention that a bigger score means "more suspicious."
    anomaly_score = -model.score_samples(X_test)

    pr_auc = average_precision_score(y_test, anomaly_score)
    roc_auc = roc_auc_score(y_test, anomaly_score)
    print(f"{name:30s} PR-AUC={pr_auc:.4f}   ROC-AUC={roc_auc:.4f}   n_features={X_train.shape[1]}")
    return {"pr_auc": pr_auc, "roc_auc": roc_auc, "n_features": int(X_train.shape[1])}


print(f"train rows: {len(train)}   test rows: {len(test)}")
print()
population_only = run(include_entity=False, name="population-only")
combined = run(include_entity=True, name="population + entity-deviation")

lift = combined["pr_auc"] - population_only["pr_auc"]
print()
print(f"PR-AUC lift (combined - population-only): {lift:+.4f}")

# Diagnostic 1: is the lift hidden behind fingerprint-collision mega-clusters?
# (rejected hypothesis, kept here so the check is reproducible, not just asserted)
print()
print("diagnostic: lift when restricted to smaller, more-plausibly-real entities")
X_train_pop = pipeline.transform(train, include_entity=False)
X_test_pop = pipeline.transform(test, include_entity=False)
X_train_combined = pipeline.transform(train, include_entity=True)
X_test_combined = pipeline.transform(test, include_entity=True)

pop_model = IsolationForest(n_estimators=200, contamination="auto", random_state=42, n_jobs=-1).fit(X_train_pop)
combined_model = IsolationForest(n_estimators=200, contamination="auto", random_state=42, n_jobs=-1).fit(X_train_combined)
pop_score_test = -pop_model.score_samples(X_test_pop)
combined_score_test = -combined_model.score_samples(X_test_combined)

mega_cluster_check = {}
for cap in [20, 50]:
    mask = (test["entity_prior_count"] <= cap).to_numpy()
    pop_pr = average_precision_score(y_test[mask], pop_score_test[mask])
    combined_pr = average_precision_score(y_test[mask], combined_score_test[mask])
    mega_cluster_check[f"prior_count_le_{cap}"] = {
        "rows": int(mask.sum()), "pop_pr_auc": pop_pr, "combined_pr_auc": combined_pr,
        "lift": combined_pr - pop_pr,
    }
    print(f"  prior_count<={cap}: rows={mask.sum()}  lift={combined_pr - pop_pr:+.4f}")

# Diagnostic 2: late fusion (two separate scores combined, per TDS-2), instead of
# one shared feature table (also did not show a lift, kept for reproducibility).
print()
print("diagnostic: late-fusion of population score + entity z-score")
pop_score_train = -pop_model.score_samples(X_train_pop)
entity_score_test = X_test_combined["entity_amt_zscore"].abs().to_numpy()
entity_score_train = X_train_combined["entity_amt_zscore"].abs().to_numpy()


def rank_normalize(fit_on, transform_this):
    sorted_fit = np.sort(fit_on)
    return np.searchsorted(sorted_fit, transform_this) / len(sorted_fit)


pop_rank = rank_normalize(pop_score_train, pop_score_test)
entity_rank = rank_normalize(entity_score_train, entity_score_test)
late_fusion_check = {}
for combo_name, combo in [
    ("max_rank", np.maximum(pop_rank, entity_rank)),
    ("mean_rank", (pop_rank + entity_rank) / 2),
    ("weighted_0.7_pop_0.3_entity", 0.7 * pop_rank + 0.3 * entity_rank),
]:
    pr = average_precision_score(y_test, combo)
    late_fusion_check[combo_name] = {"pr_auc": pr, "lift_vs_population_only": pr - population_only["pr_auc"]}
    print(f"  {combo_name}: PR-AUC={pr:.4f}  lift={pr - population_only['pr_auc']:+.4f}")

# Diagnostic 3: the actual explanation, fraud rate by cold-start status.
print()
print("diagnostic: fraud rate by cold-start status")
cold_start = test["entity_prior_count"] == 0
has_history = test["entity_prior_count"] >= 1
fraud_rate_cold_start = float(test.loc[cold_start, "isFraud"].mean())
fraud_rate_has_history = float(test.loc[has_history, "isFraud"].mean())
share_fraud_cold_start = float(test.loc[cold_start, "isFraud"].sum() / test["isFraud"].sum())
print(f"  fraud rate, cold-start rows: {fraud_rate_cold_start:.4f}")
print(f"  fraud rate, has-history rows: {fraud_rate_has_history:.4f}")
print(f"  share of all test fraud that is cold-start: {share_fraud_cold_start:.4f}")

Path("results").mkdir(exist_ok=True)
with open("results/day2_3_isolation_forest.json", "w") as f:
    json.dump(
        {
            "population_only": population_only,
            "combined": combined,
            "pr_auc_lift": lift,
            "mega_cluster_hypothesis_check": mega_cluster_check,
            "late_fusion_variants": late_fusion_check,
            "diagnosis": {
                "fraud_rate_cold_start_test_rows": fraud_rate_cold_start,
                "fraud_rate_has_history_test_rows": fraud_rate_has_history,
                "share_of_test_fraud_that_is_cold_start": share_fraud_cold_start,
                "conclusion": (
                    "Entity-deviation shows no lift under joint-feature or late-fusion "
                    "strategies. Fraud is heavily concentrated in cold-start transactions "
                    "(no entity history yet), which an entity-deviation feature cannot "
                    "see by construction, and IsolationForest is unsupervised so it can't "
                    "learn to exploit entity_has_history's correlation with the label "
                    "even though the flag is present. Validates TDS-3's choice to surface "
                    "cold-start as an explicit typology tag rather than an implicit feature."
                ),
            },
        },
        f,
        indent=2,
    )
print("\nsaved to results/day2_3_isolation_forest.json")
