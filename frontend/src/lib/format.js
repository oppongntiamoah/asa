export const money = (v) =>
  v === null || v === undefined ? "—" : `GHS ${Number(v).toLocaleString("en-GH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export const pct = (v) => (v === null || v === undefined ? "—" : `${v >= 0 ? "+" : ""}${Number(v).toFixed(2)}%`);

export const num = (v) => (v === null || v === undefined ? "—" : Number(v).toLocaleString("en-GH"));

export const pctColor = (v) => (v === null || v === undefined ? "" : v >= 0 ? "text-emerald-600" : "text-red-600");
