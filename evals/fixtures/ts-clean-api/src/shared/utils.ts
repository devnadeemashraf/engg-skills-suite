export function normaliseName(name: string): string {
  return name.trim().replace(/\s+/g, " ");
}

export function formatCurrency(cents: number, currency: string): string {
  return `${(cents / 100).toFixed(2)} ${currency}`;
}
