export function money(millions: number | null | undefined): string {
  if (millions == null) return "Not in this table";
  const abs = Math.abs(millions);
  if (abs >= 1000) return `$${(millions / 1000).toFixed(1)} billion`;
  if (abs >= 100) return `$${Math.round(millions).toLocaleString("en-US")} million`;
  return `$${millions.toFixed(1)} million`;
}

export function moneyTile(millions: number | null | undefined): string {
  if (millions == null) return "No spending line";
  if (millions >= 1000) return `$${(millions / 1000).toFixed(1)}B`;
  if (millions >= 100) return `$${Math.round(millions)}M`;
  return `$${millions.toFixed(1)}M`;
}

export function people(value: number): string {
  return value.toLocaleString("en-US");
}

export function esc(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
