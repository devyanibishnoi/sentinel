"""Day 1 exit criterion: the four mandatory baselines, population + entity
level, precision/recall/FPR on the held-out TEST split. Thresholds are
tuned on VAL only, per docs/03_DATA_AND_EVALUATION.md §7. Nothing here is
tuned on test.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.baselines import (
    add_entity_prior_stats,
    entity_rule_flags,
    entity_zscore_flags,
    population_rule_flags,
    population_zscore_flags,
    random_baseline_flags,
)
from sentinel.entities import add_entity_id
from sentinel.metrics import evaluate
from sentinel.splitting import add_split_column

AMOUNT = "TransactionAmt"

transactions = pd.read_csv("data/raw/train_transaction.csv")
transactions = add_entity_id(transactions)
transactions = add_split_column(transactions)
transactions = add_entity_prior_stats(transactions)

train = transactions[transactions["split"] == "train"]
val = transactions[transactions["split"] == "val"]
test = transactions[transactions["split"] == "test"]

results = []


def record(name, y_true, y_pred, note=""):
    m = evaluate(y_true, y_pred)
    m["baseline"] = name
    m["note"] = note
    results.append(m)


# 1. Random / prior baseline -------------------------------------------------
train_fraud_rate = train["isFraud"].mean()
random_flags = random_baseline_flags(len(test), train_fraud_rate)
record("random_prior", test["isFraud"], random_flags,
       f"fraud_rate={train_fraud_rate:.4f} from train")

# 2. Rule baseline, population level -----------------------------------------
best = None
for pct in [0.90, 0.95, 0.99, 0.995]:
    threshold = train[AMOUNT].quantile(pct)
    val_flags = population_rule_flags(val[AMOUNT], threshold)
    m = evaluate(val["isFraud"], val_flags)
    f1 = 2 * m["precision"] * m["recall"] / (m["precision"] + m["recall"]) if (m["precision"] + m["recall"]) else 0
    if best is None or f1 > best[0]:
        best = (f1, pct, threshold)
_, best_pct, best_threshold = best
test_flags = population_rule_flags(test[AMOUNT], best_threshold)
record("rule_population", test["isFraud"], test_flags,
       f"amount > train p{best_pct} = {best_threshold:.2f} (chosen on val)")

# 3. Statistical baseline, population level ----------------------------------
train_mean, train_std = train[AMOUNT].mean(), train[AMOUNT].std()
best = None
for cutoff in [2, 2.5, 3, 3.5, 4]:
    val_flags = population_zscore_flags(val[AMOUNT], train_mean, train_std, cutoff)
    m = evaluate(val["isFraud"], val_flags)
    f1 = 2 * m["precision"] * m["recall"] / (m["precision"] + m["recall"]) if (m["precision"] + m["recall"]) else 0
    if best is None or f1 > best[0]:
        best = (f1, cutoff)
_, best_cutoff = best
test_flags = population_zscore_flags(test[AMOUNT], train_mean, train_std, best_cutoff)
record("statistical_population", test["isFraud"], test_flags,
       f"|z| > {best_cutoff} vs train mean/std (chosen on val)")

# 4. Rule baseline, entity level ----------------------------------------------
has_history = test["entity_prior_count"] >= 1
cold_start_share = 1 - has_history.mean()
test_flags = entity_rule_flags(test)
record("rule_entity", test.loc[has_history, "isFraud"], test_flags[has_history],
       f"new record-high amount for this entity; {cold_start_share:.1%} of test rows are cold-start, excluded")

# 5. Statistical baseline, entity level ---------------------------------------
best = None
for cutoff in [2, 2.5, 3, 3.5, 4]:
    val_has_history = val["entity_prior_count"] >= 2
    val_flags = entity_zscore_flags(val, cutoff)
    m = evaluate(val.loc[val_has_history, "isFraud"], val_flags[val_has_history])
    f1 = 2 * m["precision"] * m["recall"] / (m["precision"] + m["recall"]) if (m["precision"] + m["recall"]) else 0
    if best is None or f1 > best[0]:
        best = (f1, cutoff)
_, best_cutoff = best
has_history_2 = test["entity_prior_count"] >= 2
cold_start_share_2 = 1 - has_history_2.mean()
test_flags = entity_zscore_flags(test, best_cutoff)
record("statistical_entity", test.loc[has_history_2, "isFraud"], test_flags[has_history_2],
       f"|z| > {best_cutoff} vs this entity's own prior mean/std (chosen on val); "
       f"{cold_start_share_2:.1%} of test rows lack 2+ prior transactions, excluded")

results_df = pd.DataFrame(results)[
    ["baseline", "precision", "recall", "fpr", "tp", "fp", "fn", "tn", "note"]
]
pd.set_option("display.width", 160)
pd.set_option("display.max_colwidth", 80)
print(results_df.to_string(index=False))

Path("results").mkdir(exist_ok=True)
results_df.to_csv("results/day1_baselines.csv", index=False)
print("\nsaved to results/day1_baselines.csv")
