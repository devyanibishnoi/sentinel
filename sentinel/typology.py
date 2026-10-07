"""Typology tagging (TDS-3): descriptive, unscored, rule-based.

Explains a detection in plain language, it does not feed the
Orchestrator's confidence gate (ADR-0007), that's score_population and
ring membership only. This exists purely for human-readable "why this
might be worth a look."

Priority when more than one tag could apply, highest first:
device_mismatch > amount_deviation > cold_start > None. Device mismatch
is the most specific, concrete signal; cold_start is the weakest (just
"we don't know much yet"), so it only shows up when nothing sharper
applies.
"""

import numpy as np
import pandas as pd

from sentinel.features import _add_derived

AMOUNT_ZSCORE_THRESHOLD = 3.0
AMOUNT_RATIO_THRESHOLD = 3.0


def add_device_mismatch_flag(
    df: pd.DataFrame,
    entity_col: str = "entity_id",
    device_col: str = "DeviceInfo",
    time_col: str = "TransactionDT",
) -> pd.DataFrame:
    """True if this transaction's device was never seen before for this
    entity, using only strictly-earlier transactions (same leakage-safe
    pattern as sentinel.baselines.add_entity_prior_stats)."""
    df = df.sort_values([entity_col, time_col]).copy()

    seen_devices: dict[str, set] = {}
    mismatch = np.zeros(len(df), dtype=bool)
    for i, (entity_id, device) in enumerate(zip(df[entity_col], df[device_col])):
        if pd.isna(device):
            continue
        prior = seen_devices.get(entity_id)
        if prior is not None and device not in prior:
            mismatch[i] = True
        seen_devices.setdefault(entity_id, set()).add(device)

    df["device_mismatch"] = mismatch
    return df


def add_typology_tag(df: pd.DataFrame) -> pd.DataFrame:
    df = add_device_mismatch_flag(df)
    df = _add_derived(df)

    has_full_stats = df["entity_prior_count"] >= 2
    has_history = df["entity_prior_count"] >= 1
    is_cold_start = df["entity_prior_count"] == 0

    amount_deviation = (has_full_stats & (df["entity_amt_zscore"].abs() > AMOUNT_ZSCORE_THRESHOLD)) | (
        has_history & (df["entity_amt_vs_prior_max_ratio"] > AMOUNT_RATIO_THRESHOLD)
    )

    tag = pd.Series(None, index=df.index, dtype=object)
    tag[is_cold_start] = "cold_start"
    tag[amount_deviation] = "amount_deviation"
    tag[df["device_mismatch"]] = "device_mismatch"

    df["typology_tag"] = tag
    return df
