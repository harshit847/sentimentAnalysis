import type { FaceResult } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export function getApiBase() {
  return API_BASE;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("token", token);
  else localStorage.removeItem("token");
}

async function parseError(res: Response): Promise<string> {
  const data = await res.json().catch(() => ({} as { detail?: unknown }));
  const d = data.detail;
  if (Array.isArray(d)) {
    return d.map((x: { msg?: string }) => x.msg || "").filter(Boolean).join("; ");
  }
  if (typeof d === "string") return d;
  return res.statusText || "Request failed";
}

export type ApiOptions = RequestInit & { json?: unknown; skipAuth?: boolean };

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { json, skipAuth, headers: initHeaders, ...rest } = options;
  const headers = new Headers(initHeaders);

  if (json !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (!skipAuth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers,
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });

  if (!res.ok) {
    throw new Error(await parseError(res));
  }

  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type");
  if (ct && ct.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return (await res.text()) as T;
}

export async function uploadFace(file: Blob, filename = "capture.jpg"): Promise<FaceResult> {
  const form = new FormData();
  form.append("file", file, filename);
  const token = getToken();
  const headers: HeadersInit = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}/analyze/face`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function downloadHistoryCsv(analysisType?: string) {
  const token = getToken();
  const q = analysisType ? `?analysis_type=${encodeURIComponent(analysisType)}` : "";
  const res = await fetch(`${API_BASE}/history/export/csv${q}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(await parseError(res));
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sentiment-history.csv";
  a.click();
  URL.revokeObjectURL(url);
}
