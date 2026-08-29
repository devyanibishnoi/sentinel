"""Feature pipeline for the real detector (TDS-1, TDS-2).

Population features: amount, time-of-day, card/address identifiers, and
Vesta's C1-C14 count features. Deliberately not the full 394-column
dataset, the D/M/V engineered columns have messier missingness and
weren't worth the time against today's target, that's a named
limitation, not an oversight.

Entity-deviation features reuse the same leakage-safe, prior-only
construction as the baselines (sentinel.baselines.add_entity_prior_stats
must be called on the dataframe before this pipeline sees it).

All imputation/encoding statistics are learned via fit() on train only,
then applied via transform() to any split, so nothing about val/test
ever influences how a value gets filled in or encoded.
"""

import numpy as np
import pandas as pd

POP_NUMERIC = (
    ["TransactionAmt", "hour_of_day", "card1", "card2", "card3", "card5", "addr1", "addr2"]
    + [f"C{i}" for i in range(1, 15)]
)
POP_CATEGORICAL = ["ProductCD", "card4", "card6"]
ENTITY_NUMERIC = [
    "entity_prior_count",
    "entity_has_history",
    "entity_has_full_stats",
    "entity_amt_zscore",
    "entity_amt_vs_prior_max_ratio",
]


def _add_derived(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour_of_day"] = (df["TransactionDT"] // 3600) % 24

    has_history = df["entity_prior_count"] >= 1
    has_full_stats = df["entity_prior_count"] >= 2

    std_safe = df["entity_prior_std"].replace(0, np.nan)
    zscore = (df["TransactionAmt"] - df["entity_prior_mean"]) / std_safe

    max_safe = df["entity_prior_max"].replace(0, np.nan)
    ratio_to_max = df["TransactionAmt"] / max_safe

    df["entity_has_history"] = has_history.astype(int)
    df["entity_has_full_stats"] = has_full_stats.astype(int)
    # No history / no full stats -> neutral value (0 deviation, ratio of 1),
    # the has_history/has_full_stats flags tell the model whether to trust it.
    df["entity_amt_zscore"] = zscore.where(has_full_stats, 0.0).fillna(0.0)
    df["entity_amt_vs_prior_max_ratio"] = ratio_to_max.where(has_history, 1.0).fillna(1.0)

    return df


class FeaturePipeline:
    def __init__(self):
        self.medians_ = {}
        self.categories_ = {}

    def fit(self, train_df: pd.DataFrame) -> "FeaturePipeline":
        derived = _add_derived(train_df)
        for col in POP_NUMERIC:
            self.medians_[col] = derived[col].median()
        for col in POP_CATEGORICAL:
            self.categories_[col] = derived[col].astype("category").cat.categories
        return self

    def transform(self, df: pd.DataFrame, include_entity: bool = True) -> pd.DataFrame:
        derived = _add_derived(df)
        feature_cols = []

        for col in POP_NUMERIC:
            derived[col] = derived[col].fillna(self.medians_[col])
            feature_cols.append(col)

        for col in POP_CATEGORICAL:
            coded = pd.Categorical(derived[col], categories=self.categories_[col]).codes
            derived[col + "_code"] = coded
            feature_cols.append(col + "_code")

        if include_entity:
            feature_cols += ENTITY_NUMERIC

        return derived[feature_cols]
