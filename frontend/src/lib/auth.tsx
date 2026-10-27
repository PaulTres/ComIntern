"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { UNAUTHORIZED_EVENT, api, getToken, json, setToken } from "@/lib/api";
import type { User } from "@/lib/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, password: string, companyName: string) => Promise<User>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchMe = () => (getToken() ? api<User>("/auth/me").catch(() => null) : Promise.resolve(null));

  const refresh = useCallback(async () => setUser(await fetchMe()), []);

  useEffect(() => {
    fetchMe().then((u) => {
      setUser(u);
      setLoading(false);
    });
    // An expired token anywhere signs the user out; RequireAuth then redirects to /login.
    const onUnauthorized = () => setUser(null);
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  const authenticate = async (path: string, body: object) => {
    const res = await api<{ access_token: string; user: User }>(path, { method: "POST", body: json(body) });
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  };

  const value: AuthState = {
    user,
    loading,
    login: (email, password) => authenticate("/auth/login", { email, password }),
    register: (email, password, companyName) =>
      authenticate("/auth/register", { email, password, company_name: companyName }),
    logout: () => {
      setToken(null);
      setUser(null);
      router.push("/");
    },
    refresh,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
