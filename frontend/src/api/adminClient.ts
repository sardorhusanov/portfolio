import type { Admin } from "../types/admin";
const base =
  (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "") + "/admin";
let accessToken: string | null = null;
let snapshot: { admin: Admin | null; ready: boolean } = {
  admin: null,
  ready: false,
};
const listeners = new Set<() => void>();
let refreshing: Promise<boolean> | null = null;
export class AdminError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export const sessionStore = {
  getSnapshot: () => snapshot,
  subscribe: (fn: () => void) => {
    listeners.add(fn);
    return () => {
      listeners.delete(fn);
    };
  },
};
function setSession(admin: Admin | null, token: string | null) {
  accessToken = token;
  snapshot = { admin, ready: true };
  listeners.forEach((fn) => fn());
}
async function parseError(response: Response): Promise<AdminError> {
  let message = "The request could not be completed. Please try again.";
  try {
    const body = (await response.json()) as {
      detail?: string | { loc: string[]; msg: string }[];
    };
    if (typeof body.detail === "string") message = body.detail;
    else if (Array.isArray(body.detail))
      message = body.detail
        .map((item) => `${item.loc.at(-1)}: ${item.msg}`)
        .join(". ");
  } catch {
    /* Use the safe fallback. */
  }
  return new AdminError(response.status, message);
}
async function refreshRequest(): Promise<boolean> {
  try {
    const response = await fetch(base + "/auth/refresh", {
      method: "POST",
      credentials: "include",
      headers: { "X-CSRF-Protection": "1" },
    });
    if (!response.ok) {
      setSession(null, null);
      return false;
    }
    const data = (await response.json()) as {
      admin: Admin;
      access_token: string;
    };
    setSession(data.admin, data.access_token);
    return true;
  } catch {
    setSession(null, null);
    return false;
  }
}
export function refreshSession(): Promise<boolean> {
  if (!refreshing) {
    const job = async (): Promise<boolean> => {
      if (navigator.locks)
        return await navigator.locks.request(
          "portfolio-session-refresh",
          refreshRequest,
        );
      return await refreshRequest();
    };
    refreshing = job().finally(() => {
      refreshing = null;
    });
  }
  return refreshing;
}
export async function ensureSession() {
  if (!snapshot.ready) await refreshSession();
}
export async function login(email: string, password: string) {
  const response = await fetch(base + "/auth/login", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", "X-CSRF-Protection": "1" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw await parseError(response);
  const data = (await response.json()) as {
    admin: Admin;
    access_token: string;
  };
  setSession(data.admin, data.access_token);
}
export async function logout() {
  const response = await fetch(base + "/auth/logout", {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Protection": "1" },
  });
  if (!response.ok) throw await parseError(response);
  setSession(null, null);
}
export async function adminRequest<T>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(base + path, { ...init, headers });
  if (response.status === 401 && retry && (await refreshSession()))
    return adminRequest<T>(path, init, false);
  if (!response.ok) {
    if (response.status === 401) setSession(null, null);
    throw await parseError(response);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
