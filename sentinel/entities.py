"""Proxy entity_id reconstruction (ADR-0002, TDS-1).

Not verified ground truth. A row missing any key field gets its own
unique entity_id rather than colliding with other missing rows, see
docs/LEARNING_LOG.md for why that matters.
"""

import pandas as pd

KEY_FIELDS = ["card1", "card2", "card3", "card4", "card5", "card6", "addr1", "addr2"]


def add_entity_id(transactions: pd.DataFrame) -> pd.DataFrame:
    transactions = transactions.copy()

    has_missing_key_field = transactions[KEY_FIELDS].isna().any(axis=1)

    combined_key = (
        transactions[KEY_FIELDS].fillna("missing").astype(str).agg("_".join, axis=1)
    )

    transactions["entity_id"] = combined_key.where(
        ~has_missing_key_field,
        "unmatched_" + transactions["TransactionID"].astype(str),
    )

    return transactions
