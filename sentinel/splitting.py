"""Entity-level train/val/test split (Data & Eval spec §3, §7).

An entity's transactions stay entirely in one split, never spread across
splits, see docs/03_DATA_AND_EVALUATION.md and CLAUDE.md's own leakage
example for why this is non-negotiable.
"""

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


def add_split_column(
    transactions: pd.DataFrame,
    entity_col: str = "entity_id",
    test_size: float = 0.2,
    val_size: float = 0.2,
    random_state: int = 42,
) -> pd.DataFrame:
    transactions = transactions.copy()
    groups = transactions[entity_col]

    # Step 1: carve off the test split by entity.
    test_splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_val_idx, test_idx = next(test_splitter.split(transactions, groups=groups))

    # Step 2: carve val out of what's left, still grouping by entity.
    remainder = transactions.iloc[train_val_idx]
    val_splitter = GroupShuffleSplit(n_splits=1, test_size=val_size, random_state=random_state)
    train_idx, val_idx = next(
        val_splitter.split(remainder, groups=remainder[entity_col])
    )

    split = pd.Series("train", index=transactions.index)
    split.iloc[test_idx] = "test"
    split.iloc[train_val_idx[val_idx]] = "val"
    transactions["split"] = split

    return transactions
