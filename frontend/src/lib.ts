import { useEffect } from "react";
import { api, getStoredAuth } from "./api/client";

export function longDate(isoDate: string): string {
  const d = new Date(`${isoDate}T00:00:00`);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function todayIso(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return "Never";
  return new Date(iso).toLocaleString();
}

let lastTracked = { key: "", at: 0 };

/**
 * Records an anonymous page view for the public pages. The server sets a first-party
 * cookie to tell visitors apart. Signed-in staff are not counted, so internal browsing
 * doesn't inflate the numbers. Failures are ignored on purpose.
 */
export function useTrackVisit(newsletterId?: number): void {
  useEffect(() => {
    if (getStoredAuth()) return;
    const key = `${window.location.pathname}|${newsletterId ?? ""}`;
    const now = Date.now();
    // React StrictMode runs effects twice in dev; don't double count.
    if (lastTracked.key === key && now - lastTracked.at < 3000) return;
    lastTracked = { key, at: now };
    api
      .post("/track/visit", { path: window.location.pathname, newsletter_id: newsletterId ?? null })
      .catch(() => undefined);
  }, [newsletterId]);
}
