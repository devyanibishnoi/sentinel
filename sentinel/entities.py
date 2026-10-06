"""Proxy entity_id reconstruction (ADR-0002, TDS-1).

Not verified ground truth. A row missing any key field gets its own
unique entity_id rather than colliding with other missing rows, see
docs/LEARNING_LOG.md for why that matters.

D1_adjusted is a reverse-engineered-by-the-Kaggle-community trick, not an
official Vesta/IEEE field: D1 behaves like "days since this card was
first seen," and TransactionDT/86400 also increases with real time at
the same rate, so subtracting them cancels the time-passing part out,
leaving roughly a constant per real account (which day it first
appeared). Added to the fingerprint specifically to split apart entities
that share identical card/address fields but started at different times,
see LEARNING_LOG for the before/after cluster-size evidence.
"""

import pandas as pd

KEY_FIELDS = [
    "card1", "card2", "card3", "card4", "card5", "card6", "addr1", "addr2", "D1_adjusted",
]


def add_entity_id(transactions: pd.DataFrame) -> pd.DataFrame:
    transactions = transactions.copy()

    transactions["D1_adjusted"] = (transactions["TransactionDT"] // 86400) - transactions["D1"]

    has_missing_key_field = transactions[KEY_FIELDS].isna().any(axis=1)

    combined_key = (
        transactions[KEY_FIELDS].fillna("missing").astype(str).agg("_".join, axis=1)
    )

    transactions["entity_id"] = combined_key.where(
        ~has_missing_key_field,
        "unmatched_" + transactions["TransactionID"].astype(str),
    )

    return transactions
