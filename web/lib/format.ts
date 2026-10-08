export function formatInr(amount: number): string {
  return `₹${amount.toFixed(2)}`;
}

export function formatScore(score: number): string {
  return score.toFixed(3);
}

export function truncate(value: string, length: number): string {
  return value.length > length ? `${value.slice(0, length)}…` : value;
}
