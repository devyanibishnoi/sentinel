"""Unified comparison: every baseline AND both IsolationForest variants,
all scored on the SAME metric (PR-AUC), on the SAME test set, reported
both on the full test set and restricted to has-history rows only.

This is what docs/03_DATA_AND_EVALUATION.md's "every model reports its
numbers next to all four baselines, always" actually looks like when
it's one real table instead of several differently-shaped reports.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.baselines import add_entity_prior_stats
from sentinel.entities import add_entity_id
from sentinel.features import FeaturePipeline, _add_derived
from sentinel.splitting import add_split_column

transactions = pd.read_csv("data/raw/train_transaction.csv")
transactions = add_entity_id(transactions)
transactions = add_split_column(transactions)
transactions = add_entity_prior_stats(transactions)

train = transactions[transactions["split"] == "train"]
test = transactions[transactions["split"] == "test"]
y_test = test["isFraud"].to_numpy()
has_history_mask = (test["entity_prior_count"] >= 1).to_numpy()

print(f"test rows: {len(test)}   has-history rows: {has_history_mask.sum()} "
      f"({has_history_mask.mean():.1%})")
print()

# ---- continuous scores, one per method, higher = more suspicious ----
scores = {}

rng = np.random.default_rng(42)
scores["random_prior"] = rng.random(len(test))

train_mean, train_std = train["TransactionAmt"].mean(), train["TransactionAmt"].std()
scores["rule_population (raw amount)"] = test["TransactionAmt"].to_numpy()
scores["statistical_population (|z| vs population)"] = (
    ((test["TransactionAmt"] - train_mean) / train_std).abs().to_numpy()
)

test_derived = _add_derived(test)
scores["rule_entity (ratio to own prior max)"] = test_derived["entity_amt_vs_prior_max_ratio"].to_numpy()
scores["statistical_entity (|z| vs own history)"] = test_derived["entity_amt_zscore"].abs().to_numpy()

pipeline = FeaturePipeline().fit(train)
for include_entity, label in [(False, "isolation_forest (population-only)"),
                               (True, "isolation_forest (population + entity-deviation)")]:
    X_train = pipeline.transform(train, include_entity=include_entity)
    X_test = pipeline.transform(test, include_entity=include_entity)
    model = IsolationForest(n_estimators=200, contamination="auto", random_state=42, n_jobs=-1).fit(X_train)
    scores[label] = -model.score_samples(X_test)

# ---- PR-AUC, full test set AND has-history-only ----
results = []
for name, score in scores.items():
    full_pr_auc = average_precision_score(y_test, score)
    history_pr_auc = average_precision_score(y_test[has_history_mask], score[has_history_mask])
    results.append({"method": name, "pr_auc_full_test": full_pr_auc, "pr_auc_has_history_only": history_pr_auc})

results_df = pd.DataFrame(results).sort_values("pr_auc_full_test", ascending=False)
pd.set_option("display.width", 160)
pd.set_option("display.max_colwidth", 60)
print(results_df.to_string(index=False))

# Diagnostic: even among has-history rows, how much history is there really?
has_history_rows = test[has_history_mask]
exactly_one_prior = int((has_history_rows["entity_prior_count"] == 1).sum())
two_plus_prior = int((has_history_rows["entity_prior_count"] >= 2).sum())
median_prior_count = float(has_history_rows["entity_prior_count"].median())

print()
print("diagnostic: history depth among has-history rows")
print(f"  median prior-transaction-count: {median_prior_count}")
print(f"  rows with exactly 1 prior (no std computable): {exactly_one_prior} "
      f"({exactly_one_prior / len(has_history_rows):.1%} of has-history rows)")
print(f"  rows with 2+ prior (std actually defined): {two_plus_prior} "
      f"({two_plus_prior / len(has_history_rows):.1%} of has-history rows)")

Path("results").mkdir(exist_ok=True)
with open("results/full_comparison.json", "w") as f:
    json.dump(
        {
            "test_rows": len(test),
            "has_history_rows": int(has_history_mask.sum()),
            "has_history_share": float(has_history_mask.mean()),
            "results": results,
            "history_depth_diagnostic": {
                "median_prior_count_among_has_history": median_prior_count,
                "exactly_one_prior_count": exactly_one_prior,
                "exactly_one_prior_share_of_has_history": exactly_one_prior / len(has_history_rows),
                "two_plus_prior_count": two_plus_prior,
                "conclusion": (
                    "Entity-deviation shows no PR-AUC lift over population-only, even "
                    "restricted to has-history rows. Root cause: most account histories "
                    "in this dataset are too thin to baseline against, not a fingerprint "
                    "or split artifact, both were fixed and the result held."
                ),
            },
        },
        f,
        indent=2,
    )
print("\nsaved to results/full_comparison.json")
