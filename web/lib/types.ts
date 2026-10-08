export type Decision = "allow" | "review" | "decline";
export type Source = "benchmark" | "demo";

export interface Detection {
  TransactionID: string;
  entity_id: string;
  TransactionDT: number;
  TransactionAmt: number;
  score_population: number;
  score_entity_deviation: number;
  score_combined: number;
  typology_tag: string | null;
  ring_cluster_id: string | null;
  ground_truth_fraud: number | null;
  decision: Decision;
  decision_reasoning: string;
  source: Source;
}

export interface RingEdge {
  entity_id: string;
  DeviceInfo: string;
}

export interface RingCluster {
  cluster_id: string;
  entities: string[];
  n_entities: number;
  n_transactions: number;
  proxy_fraud_rate: number | null;
  avg_population_score?: number;
  edges: RingEdge[];
}

export interface ComparisonRow {
  method: string;
  pr_auc_full_test: number;
  pr_auc_has_history_only: number;
}

export interface BaselineRow {
  baseline: string;
  precision: number;
  recall: number;
  fpr: number;
  tp: number;
  fp: number;
  fn: number;
  tn: number;
  note: string;
}
