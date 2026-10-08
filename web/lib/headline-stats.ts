// Every number here traces back to results/ files, verified against
// the actual output before writing (see docs/LEARNING_LOG.md for one
// case where a remembered number was wrong and got caught before
// shipping). Keep this in sync with web/data/*.json.

export const HEADLINE = {
  testRows: 85004,
  flaggedCount: 2259,
  autoResponder: { allow: 82745, decline: 1874, review: 385 },
  popOnlyPrAuc: 0.166,
  combinedPrAuc: 0.156,
  bestBaselinePrAuc: 0.055,
  liftMultiple: 3,
  coldStartFraudShare: 0.42,
  hasHistoryShare: 0.353,
  thinHistoryShare: 0.409,
  ringCount: 70,
  bestRing: { entities: 12, fraudRate: 1.0 },
  baselineFraudRate: 0.046,
};
