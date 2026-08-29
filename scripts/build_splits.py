"""Day 1: entity-level train/val/test split, with a leakage check."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.entities import add_entity_id
from sentinel.splitting import add_split_column

transactions = pd.read_csv("data/raw/train_transaction.csv")
transactions = add_entity_id(transactions)
transactions = add_split_column(transactions)

print("rows per split:")
print(transactions["split"].value_counts())
print()

print("entities per split:")
print(transactions.groupby("split")["entity_id"].nunique())
print()

print("fraud rate per split:")
print(transactions.groupby("split")["isFraud"].mean())
print()

# Leakage check: no entity_id should ever appear in more than one split.
entities_per_split_count = transactions.groupby("entity_id")["split"].nunique()
leaking_entities = (entities_per_split_count > 1).sum()
print(f"entities appearing in more than one split: {leaking_entities}")
assert leaking_entities == 0, "entity-level split leaked, an entity spans splits"
print("no leakage: every entity's rows stayed in a single split")
