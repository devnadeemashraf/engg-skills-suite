// DEFECT D3: a whole file nothing imports.
export function legacyFormatOrderId(id: number): string {
  return "ORD-" + String(id).padStart(8, "0");
}

export function legacyParseOrderId(text: string): number {
  return Number(text.replace("ORD-", ""));
}
