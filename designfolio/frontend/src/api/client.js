const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function api(path, options = {}) {
  const token = localStorage.getItem("designfolio_token");
  const isForm = options.body instanceof FormData || options.body instanceof URLSearchParams;
  const headers = { ...(isForm ? {} : { "Content-Type": "application/json" }), ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(API + path, { ...options, headers });
  const body = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body?.detail || "Ошибка запроса");
  return body;
}
export { API };
