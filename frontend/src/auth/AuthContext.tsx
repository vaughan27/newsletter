import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  AUTH_EXPIRED_EVENT,
  api,
  getStoredAuth,
  setStoredAuth,
} from "../api/client";
import type { LoginResponse, Role, User } from "../api/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(() => getStoredAuth() !== null);

  const logout = useCallback(() => {
    setStoredAuth(null);
    setUser(null);
    setExpiresAt(null);
  }, []);

  // Restore a session on page load.
  useEffect(() => {
    const stored = getStoredAuth();
    if (!stored) return;
    let cancelled = false;
    api
      .get<User>("/auth/me")
      .then((u) => {
        if (cancelled) return;
        setUser(u);
        setExpiresAt(stored.expiresAt);
      })
      .catch(() => {
        if (!cancelled) logout();
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [logout]);

  // Any 401 from the API (expired/revoked token) signs the user out.
  useEffect(() => {
    window.addEventListener(AUTH_EXPIRED_EVENT, logout);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, logout);
  }, [logout]);

  // Sign out exactly when the 8-hour token expires, even if the tab stays open.
  useEffect(() => {
    if (!expiresAt) return;
    const ms = new Date(expiresAt).getTime() - Date.now();
    if (ms <= 0) {
      logout();
      return;
    }
    const id = window.setTimeout(logout, Math.min(ms, 2_147_000_000));
    return () => window.clearTimeout(id);
  }, [expiresAt, logout]);

  const login = useCallback(async (username: string, password: string) => {
    const res = await api.post<LoginResponse>("/auth/login", { username, password });
    setStoredAuth({ token: res.access_token, expiresAt: res.expires_at });
    setUser(res.user);
    setExpiresAt(res.expires_at);
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      login,
      logout,
      hasRole: (...roles: Role[]) => user !== null && roles.includes(user.role),
    }),
    [user, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
