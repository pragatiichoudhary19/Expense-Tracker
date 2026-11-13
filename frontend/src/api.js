const BASE = import.meta.env.VITE_API_URL || "/api";
const TOKEN_KEY = "spendwise_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY));

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function errorMessage(data, fallback) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => `${(d.loc || []).slice(1).join(".")}: ${d.msg}`).join("; ");
  }
  return fallback;
}

async function request(path, { method = "GET", body, form, params } = {}) {
  const url = new URL(BASE + path, window.location.origin);
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });

  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = form;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(url, { method, headers, body: payload });
  } catch {
    throw new ApiError("Cannot reach the server. Is the backend running?", 0);
  }

  if (res.status === 401 && token) {
    setToken(null);
    window.dispatchEvent(new Event("spendwise:logout"));
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(errorMessage(data, `Request failed (${res.status})`), res.status);
  return data;
}

export const api = {
  register: (body) => request("/auth/register", { method: "POST", body }),
  login: (body) => request("/auth/login", { method: "POST", body }),
  me: () => request("/auth/me"),
  categories: () => request("/expenses/categories"),
  suggestCategory: (text) => request("/expenses/categorize", { method: "POST", body: { text } }),
  listExpenses: (params) => request("/expenses", { params }),
  createExpense: (body) => request("/expenses", { method: "POST", body }),
  updateExpense: (id, body) => request(`/expenses/${id}`, { method: "PUT", body }),
  deleteExpense: (id) => request(`/expenses/${id}`, { method: "DELETE" }),
  budgets: (month) => request("/budgets", { params: { month } }),
  saveBudget: (body) => request("/budgets", { method: "PUT", body }),
  deleteBudget: (category) => request(`/budgets/${encodeURIComponent(category)}`, { method: "DELETE" }),
  summary: (month) => request("/analytics/summary", { params: { month } }),
  scanReceipt: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/receipts/scan", { method: "POST", form });
  },
};
