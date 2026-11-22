const API_BASE = "/newsletter-api";
const AUTH_KEY = "newsletter_portal_auth";
export const AUTH_EXPIRED_EVENT = "auth:expired";

export interface StoredAuth {
  token: string;
  expiresAt: string;
}

export function getStoredAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    if (!raw) return null;
    const auth = JSON.parse(raw) as StoredAuth;
    if (new Date(auth.expiresAt).getTime() <= Date.now()) {
      localStorage.removeItem(AUTH_KEY);
      return null;
    }
    return auth;
  } catch {
    return null;
  }
}

export function setStoredAuth(auth: StoredAuth | null): void {
  try {
    if (auth) localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
    else localStorage.removeItem(AUTH_KEY);
  } catch {
    /* storage unavailable (private mode); session simply won't persist */
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function formatDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        if (d && typeof d === "object" && "msg" in d) {
          const loc = (d as { loc?: unknown[] }).loc;
          const field = Array.isArray(loc) ? String(loc[loc.length - 1]) : "";
          const msg = String((d as { msg: unknown }).msg);
          return field && field !== "body" ? `${field}: ${msg}` : msg;
        }
        return String(d);
      })
      .join(" · ");
  }
  return "Something went wrong. Please try again.";
}

function handleFailure(status: number, body: unknown, hadToken: boolean): ApiError {
  if (status === 401 && hadToken) {
    setStoredAuth(null);
    window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
  }
  const detail = body && typeof body === "object" ? (body as { detail?: unknown }).detail : undefined;
  return new ApiError(status, formatDetail(detail));
}

async function request<T>(method: string, path: string, json?: unknown): Promise<T> {
  const auth = getStoredAuth();
  const headers: Record<string, string> = {};
  if (auth) headers.Authorization = `Bearer ${auth.token}`;
  if (json !== undefined) headers["Content-Type"] = "application/json";

  let res: Response;
  try {
    res = await fetch(API_BASE + path, {
      method,
      headers,
      body: json !== undefined ? JSON.stringify(json) : undefined,
      credentials: "same-origin",
    });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }

  if (res.status === 204) return undefined as T;
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) throw handleFailure(res.status, body, auth !== null);
  return body as T;
}

/** Multipart upload with progress (fetch can't report upload progress). */
export function sendForm<T>(
  method: "POST" | "PATCH",
  path: string,
  form: FormData,
  onProgress?: (percent: number) => void,
): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const auth = getStoredAuth();
    const xhr = new XMLHttpRequest();
    xhr.open(method, API_BASE + path);
    if (auth) xhr.setRequestHeader("Authorization", `Bearer ${auth.token}`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      let body: unknown = null;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        /* non-JSON body */
      }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as T);
      else reject(handleFailure(xhr.status, body, auth !== null));
    };
    xhr.onerror = () =>
      reject(new ApiError(0, "Upload failed. Check your connection and try again."));
    xhr.send(form);
  });
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, json?: unknown) => request<T>("POST", path, json),
  patch: <T>(path: string, json?: unknown) => request<T>("PATCH", path, json),
  del: (path: string) => request<void>("DELETE", path),
};
