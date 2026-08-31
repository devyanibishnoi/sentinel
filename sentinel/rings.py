"""Ring detection: shared-fingerprint graph, connected components (TDS-4).

Entities are nodes. A fingerprint value (e.g. one DeviceInfo string) is
ALSO a node, and gets an edge to every entity that used it, but only if
that fingerprint is shared by a plausible NUMBER of entities, not too few
(useless, singleton) and not too many (a generic value, the exact
"one popular shared fingerprint" failure mode named in TDS-4).

Cluster proxy fraud rate is NOT verified ground truth. Say so every time
it's shown, not just once (project non-negotiable, CLAUDE.md).
"""

import networkx as nx
import pandas as pd


def build_fingerprint_graph(
    df: pd.DataFrame,
    fingerprint_col: str,
    entity_col: str = "entity_id",
    min_entities_per_fingerprint: int = 2,
    max_entities_per_fingerprint: int = 20,
) -> nx.Graph:
    with_fingerprint = df.dropna(subset=[fingerprint_col])[[entity_col, fingerprint_col]].drop_duplicates()

    entities_per_value = with_fingerprint.groupby(fingerprint_col)[entity_col].nunique()
    usable_values = entities_per_value[
        (entities_per_value >= min_entities_per_fingerprint)
        & (entities_per_value <= max_entities_per_fingerprint)
    ].index

    graph = nx.Graph()
    usable = with_fingerprint[with_fingerprint[fingerprint_col].isin(usable_values)]
    for entity_id, fingerprint_value in usable.itertuples(index=False):
        fingerprint_node = f"{fingerprint_col}::{fingerprint_value}"
        graph.add_edge(entity_id, fingerprint_node)

    return graph


def find_clusters(graph: nx.Graph, min_size: int = 2, max_size: int = 50) -> list[set[str]]:
    """Returns entity-only clusters (fingerprint nodes stripped out),
    keeping only clusters with min_size <= n_entities <= max_size.

    max_size guards against connected-component chaining: even after
    capping how many entities a single fingerprint value can have,
    components can still balloon by chaining through many individually
    small, distinct fingerprints. An oversized component is much more
    likely to be shared infrastructure noise than a real ring, see
    docs/LEARNING_LOG.md for the below-baseline-fraud-rate evidence that
    motivated this cap."""
    clusters = []
    for component in nx.connected_components(graph):
        entities_only = {node for node in component if "::" not in node}
        if min_size <= len(entities_only) <= max_size:
            clusters.append(entities_only)
    return clusters


def score_cluster(cluster_entities: set[str], transactions: pd.DataFrame, entity_col: str = "entity_id") -> dict:
    """Proxy fraud rate for one cluster. NOT verified ground truth, this
    is a derived proxy label, say so wherever this is displayed."""
    cluster_rows = transactions[transactions[entity_col].isin(cluster_entities)]
    return {
        "n_entities": len(cluster_entities),
        "n_transactions": len(cluster_rows),
        "proxy_fraud_rate": float(cluster_rows["isFraud"].mean()),
        "n_fraud_transactions": int(cluster_rows["isFraud"].sum()),
        "caveat": "proxy fraud rate is NOT verified ground truth, a derived signal only",
    }
