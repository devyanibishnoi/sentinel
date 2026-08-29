"""The four mandatory baselines, at population and entity level
(docs/03_DATA_AND_EVALUATION.md §4). These exist so a real model has an
honest number to beat, not to be clever.
"""

import numpy as np
import pandas as pd


def random_baseline_flags(n_rows: int, fraud_rate: float, random_state: int = 42) -> np.ndarray:
    """Flags fraud independently at the same rate fraud actually occurs in train.
    The floor every other baseline has to clear."""
    rng = np.random.default_rng(random_state)
    return rng.random(n_rows) < fraud_rate


def add_entity_prior_stats(
    df: pd.DataFrame,
    amount_col: str = "TransactionAmt",
    time_col: str = "TransactionDT",
    entity_col: str = "entity_id",
) -> pd.DataFrame:
    """For each row, stats computed ONLY from that same entity's strictly
    earlier transactions (within whatever split this df is), never
    including the current row or anything from another split."""
    df = df.sort_values([entity_col, time_col]).copy()
    grouped = df.groupby(entity_col)[amount_col]

    df["entity_prior_count"] = grouped.cumcount()
    df["entity_prior_max"] = grouped.transform(lambda s: s.cummax().shift(1))
    df["entity_prior_mean"] = grouped.transform(lambda s: s.expanding().mean().shift(1))
    df["entity_prior_std"] = grouped.transform(lambda s: s.expanding().std().shift(1))

    return df


def population_rule_flags(amounts: pd.Series, threshold: float) -> pd.Series:
    """Flag if amount exceeds a fixed threshold, learned from train only."""
    return amounts > threshold


def population_zscore_flags(amounts: pd.Series, mean: float, std: float, cutoff: float) -> pd.Series:
    z = (amounts - mean) / std
    return z.abs() > cutoff


def entity_rule_flags(df: pd.DataFrame, amount_col: str = "TransactionAmt") -> pd.Series:
    """Flag if this is a new record-high amount for this specific entity.
    Cold-start rows (no prior transactions) are never flagged, no
    fabricated baseline (TDS-2)."""
    has_history = df["entity_prior_count"] >= 1
    return has_history & (df[amount_col] > df["entity_prior_max"])


def entity_zscore_flags(df: pd.DataFrame, cutoff: float, amount_col: str = "TransactionAmt") -> pd.Series:
    """Flag if amount is a statistical outlier relative to this entity's
    own prior mean/std. Needs 2+ prior transactions for std to exist."""
    has_history = df["entity_prior_count"] >= 2
    z = (df[amount_col] - df["entity_prior_mean"]) / df["entity_prior_std"]
    return has_history & (z.abs() > cutoff)
