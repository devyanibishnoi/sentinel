"""Day 1: first look at IEEE-CIS. Row counts and class balance, nothing more."""

import pandas as pd

transactions = pd.read_csv("data/raw/train_transaction.csv")
print("transactions shape:", transactions.shape)

print()
print("isFraud counts:")
print(transactions["isFraud"].value_counts())

print()
print("isFraud proportions:")
print(transactions["isFraud"].value_counts(normalize=True))

identity = pd.read_csv("data/raw/train_identity.csv")
print()
print("identity shape:", identity.shape)

merged = transactions.merge(identity, on="TransactionID", how="left")
has_identity = merged["DeviceType"].notna().sum()
print()
print(f"transactions with identity data: {has_identity} / {len(merged)}")
