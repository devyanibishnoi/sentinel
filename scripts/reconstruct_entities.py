"""Day 1: proxy entity_id reconstruction + sanity check (ADR-0002).

entity_id = concatenation of stable card + address fields. Not verified
ground truth, just a proxy. This script checks whether it's trustworthy
enough to build on.
"""

import pandas as pd

transactions = pd.read_csv("data/raw/train_transaction.csv")

key_fields = ["card1", "card2", "card3", "card4", "card5", "card6", "addr1", "addr2"]

# A row missing any of these fields has nothing reliable to fingerprint it
# by, so it must not be allowed to match any other row on that missing
# value (that's the "missing == missing" collision, see LEARNING_LOG).
has_missing_key_field = transactions[key_fields].isna().any(axis=1)

# fillna before astype(str) on purpose: pandas 3.0's string dtype leaves
# missing values as an actual missing marker under astype(str) rather than
# turning them into the text "nan", so join() would crash without this.
combined_key = (
    transactions[key_fields].fillna("missing").astype(str).agg("_".join, axis=1)
)

# Rows with a complete fingerprint keep the shared combined_key (so they can
# match other rows). Rows missing a field fall back to a per-transaction ID,
# so they never accidentally merge with another incomplete row.
transactions["entity_id"] = combined_key.where(
    ~has_missing_key_field,
    "unmatched_" + transactions["TransactionID"].astype(str),
)

counts = transactions["entity_id"].value_counts()

print("total transactions:", len(transactions))
print("unique entity_ids:", counts.shape[0])
print()
print("transactions-per-entity distribution:")
print(counts.describe())
print()
print("top 10 largest entities:")
print(counts.head(10))
print()
biggest_id = counts.index[0]
biggest_share = counts.iloc[0] / len(transactions)
print(f"biggest entity_id accounts for {counts.iloc[0]} transactions "
      f"({biggest_share:.1%} of all transactions)")
print("biggest entity_id key values:", biggest_id)
