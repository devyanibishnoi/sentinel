"""Pre-check before building the ring graph: how many DISTINCT ENTITIES
share each DeviceInfo value, on the test split specifically. Row counts
are misleading here, one entity using its own phone many times isn't a
ring, this needs to be entity-level."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.entities import add_entity_id
from sentinel.splitting import add_split_column

transactions = pd.read_csv("data/raw/train_transaction.csv")
transactions = add_entity_id(transactions)
transactions = add_split_column(transactions)

identity = pd.read_csv("data/raw/train_identity.csv")[["TransactionID", "DeviceInfo"]]

test = transactions[transactions["split"] == "test"]
test_with_device = test.merge(identity, on="TransactionID", how="left")

entities_per_device = (
    test_with_device.dropna(subset=["DeviceInfo"])
    .groupby("DeviceInfo")["entity_id"]
    .nunique()
    .sort_values(ascending=False)
)

print("test rows with a DeviceInfo value:", test_with_device["DeviceInfo"].notna().sum(),
      "/", len(test_with_device))
print()
print("top 15 DeviceInfo values by DISTINCT entity count:")
print(entities_per_device.head(15))
print()
print("distinct-entities-per-device distribution:")
print(entities_per_device.describe())
print()
print("device values shared by exactly 2 entities:", (entities_per_device == 2).sum())
print("device values shared by 2-5 entities:", ((entities_per_device >= 2) & (entities_per_device <= 5)).sum())
print("device values shared by 6-20 entities:", ((entities_per_device >= 6) & (entities_per_device <= 20)).sum())
print("device values shared by 20+ entities:", (entities_per_device > 20).sum())
