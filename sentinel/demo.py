"""Demo Adapter (TDS-1b): synthetic, payment-gateway-shaped transactions
for the console demo. Never used to fit anything, only scored with the
already-trained model (scripts/fit_pipeline.py). Tagged source="demo"
at generation time (Architecture §4), so the benchmark/demo separation
is enforced in the data itself, not left to application code to remember.

Entities are bootstrapped from real train-data feature distributions
(so amounts, card types, etc. look like real payment-gateway traffic),
with fresh IDs/timestamps, never copied wholesale as one real person's
exact record. A small ring of entities deliberately share one
obviously-synthetic device string, so there's something real for the
ring detector to catch.
"""

import numpy as np
import pandas as pd

RAW_FEATURE_COLS = (
    ["TransactionAmt", "TransactionDT", "D1", "card1", "card2", "card3", "card4", "card5", "card6",
     "addr1", "addr2", "ProductCD"]
    + [f"C{i}" for i in range(1, 15)]
)

DEMO_RING_DEVICE = "SM-DEMO01 Build/INJECTEDRING"


def generate_demo_transactions(
    train: pd.DataFrame,
    n_entities: int = 60,
    ring_size: int = 7,
    start_transaction_id: int = 90_000_000,
    random_state: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    # Start the demo stream the day after the real data ends, so it reads
    # chronologically as "new" traffic, not backfilled into the past.
    start_dt = int(train["TransactionDT"].max()) + 86_400

    donors = train[RAW_FEATURE_COLS].sample(n=n_entities, random_state=random_state).reset_index(drop=True)

    rows = []
    txn_id = start_transaction_id
    dt = start_dt
    for i in range(n_entities):
        template = donors.iloc[i].to_dict()
        is_ring_member = i < ring_size
        n_txns = int(rng.integers(1, 4))

        for _ in range(n_txns):
            row = dict(template)
            row["TransactionID"] = txn_id
            row["TransactionDT"] = dt
            row["TransactionAmt"] = max(1.0, template["TransactionAmt"] * float(rng.uniform(0.7, 1.3)))
            row["DeviceInfo"] = DEMO_RING_DEVICE if is_ring_member else None
            row["demo_injected_ring"] = is_ring_member
            rows.append(row)
            txn_id += 1
            dt += int(rng.integers(300, 7200))  # a few minutes to a couple hours apart

    demo = pd.DataFrame(rows)
    # np.nan, not pd.NA: keeps the column a plain float64 so .mean()/.sum()
    # elsewhere degrade gracefully to NaN instead of raising on a
    # non-numeric dtype. No real ground truth either way, this stream is
    # never scored (Architecture §2).
    demo["isFraud"] = np.nan
    demo["source"] = "demo"
    return demo
