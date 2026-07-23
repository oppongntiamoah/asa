// Thin fetch wrapper for the session-authenticated Django API. The SPA and
// API share an origin (Vite's dev proxy locally, Django's own static files
// in prod), so cookies just work — no token storage, no CORS setup.

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export class ApiError extends Error {
  constructor(message, status, body) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

async function request(path, options = {}) {
  const method = options.method || "GET";
  const headers = { ...(options.headers || {}) };
  const isFormData = options.body instanceof FormData;

  if (method !== "GET") {
    // Django's CSRF cookie is set by GET /api/csrf/, which the app calls
    // once on startup (see main.js).
    const csrfToken = getCookie("csrftoken");
    if (csrfToken) headers["X-CSRFToken"] = csrfToken;
    // Leave Content-Type unset for FormData — the browser fills in the
    // multipart boundary itself; setting it manually breaks the upload.
    if (options.body && !isFormData) headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`/api${path}`, {
    method,
    headers,
    credentials: "same-origin",
    body: isFormData ? options.body : options.body ? JSON.stringify(options.body) : undefined,
  });

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const message = (data && (data.detail || firstError(data.errors))) || `Request to ${path} failed (${res.status}).`;
    throw new ApiError(message, res.status, data);
  }

  return data;
}

function firstError(errors) {
  if (!errors) return null;
  const first = Object.values(errors)[0];
  if (Array.isArray(first)) return first[0];
  if (typeof first === "object") return firstError(first);
  return first;
}

export const api = {
  csrf: () => request("/csrf/"),
  login: (username, password) => request("/auth/login/", { method: "POST", body: { username, password } }),
  logout: () => request("/auth/logout/", { method: "POST" }),
  me: () => request("/auth/me/"),

  dashboard: () => request("/dashboard/"),
  holdings: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/holdings/${qs ? `?${qs}` : ""}`);
  },
  costBasis: () => request("/cost-basis/"),
  marketSummary: () => request("/market/summary/"),
  marketList: (q = "") => request(`/market/list/${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  ticker: (ticker) => request(`/market/ticker/${encodeURIComponent(ticker)}/`),

  transactions: () => request("/transactions/"),
  createTransaction: (data) => request("/transactions/", { method: "POST", body: data }),
  updateTransaction: (id, data) => request(`/transactions/${id}/`, { method: "PATCH", body: data }),
  deleteTransaction: (id) => request(`/transactions/${id}/`, { method: "DELETE" }),
  checkSellQuantity: (instrumentId, quantity, excludeId) => {
    const params = new URLSearchParams({ instrument: instrumentId, quantity });
    if (excludeId) params.set("exclude", excludeId);
    return request(`/transactions/check-sell/?${params}`);
  },
  cashBalance: () => request("/cash-balance/"),
  updateCashBalance: (amount_ghs) => request("/cash-balance/", { method: "POST", body: { amount_ghs } }),

  analysisTransactions: () => request("/analysis/transactions/"),
  analysisSectors: () => request("/analysis/sectors/"),
  analysisPerformance: () => request("/analysis/performance/"),
  analysisRisk: () => request("/analysis/risk/"),
  analysisInsights: () => request("/analysis/insights/"),
  analysisCashFlow: () => request("/analysis/cash-flow/"),
  analysisTax: () => request("/analysis/tax/"),
  analysisTimeline: () => request("/analysis/timeline/"),

  dividends: () => request("/dividends/"),
  calendar: (year, month) => request(`/calendar/?year=${year}&month=${month}`),

  watchlist: () => request("/watchlist/"),
  addWatchlist: (ticker) => request("/watchlist/", { method: "POST", body: { ticker } }),
  removeWatchlist: (id) => request(`/watchlist/${id}/`, { method: "DELETE" }),

  statements: () => request("/statements/"),
  uploadStatement: (formData) => request("/statements/", { method: "POST", body: formData }),
  statement: (id) => request(`/statements/${id}/`),
  statementRows: (id) => request(`/statements/${id}/rows/`),
  updateStatementRow: (id, rowId, data) => request(`/statements/${id}/rows/${rowId}/`, { method: "PATCH", body: data }),
  confirmStatement: (id) => request(`/statements/${id}/confirm/`, { method: "POST" }),

  billingPlans: () => request("/billing/plans/"),
  billingCredits: () => request("/billing/credits/"),
  startPurchase: (planCode) => request(`/billing/purchase/${planCode}/`, { method: "POST" }),

  profile: () => request("/account/profile/"),
  updateProfile: (data) => request("/account/profile/", { method: "PATCH", body: data }),
};
