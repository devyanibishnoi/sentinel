"""Entity-level train/val/test split (Data & Eval spec §3, §7).

An entity's transactions stay entirely in one split, never spread across
splits, see docs/03_DATA_AND_EVALUATION.md and CLAUDE.md's own leakage
example for why this is non-negotiable.

Time-based, not random: entities are ordered by their EARLIEST
transaction, train gets the earliest-appearing entities, val the next
chunk, test the latest-appearing entities. This simulates real
deployment, train on the past, test on genuinely new accounts that show
up later, rather than a random split that could put two accounts from
the exact same week on opposite sides for no principled reason.

An entity is assigned to a split by when it FIRST appeared, even though
some of its later transactions might technically fall inside another
split's time window. That's an accepted tradeoff of keeping entity
integrity (never splitting one entity's rows across splits), not a
leak, an entity's own future behavior is never used to build a
DIFFERENT entity's features or the population model's parameters.
"""

import pandas as pd


def add_split_column(
    transactions: pd.DataFrame,
    entity_col: str = "entity_id",
    time_col: str = "TransactionDT",
    test_size: float = 0.2,
    val_size: float = 0.2,
) -> pd.DataFrame:
    transactions = transactions.copy()

    first_seen = transactions.groupby(entity_col)[time_col].min().sort_values()
    entities_ordered = first_seen.index

    n_entities = len(entities_ordered)
    n_test = round(n_entities * test_size)
    n_train_val = n_entities - n_test
    n_val = round(n_train_val * val_size)
    n_train = n_train_val - n_val

    split_by_entity = pd.Series("train", index=entities_ordered)
    split_by_entity.iloc[n_train : n_train + n_val] = "val"
    split_by_entity.iloc[n_train + n_val :] = "test"

    transactions["split"] = transactions[entity_col].map(split_by_entity)
    return transactions
