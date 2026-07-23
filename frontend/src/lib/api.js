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

  if (method !== "GET") {
    // Django's CSRF cookie is set by GET /api/csrf/, which the app calls
    // once on startup (see main.js).
    const csrfToken = getCookie("csrftoken");
    if (csrfToken) headers["X-CSRFToken"] = csrfToken;
    if (options.body) headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`/api${path}`, {
    method,
    headers,
    credentials: "same-origin",
    body: options.body ? JSON.stringify(options.body) : undefined,
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
    const message = (data && data.detail) || `Request to ${path} failed (${res.status}).`;
    throw new ApiError(message, res.status, data);
  }

  return data;
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
};
