"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Loader2 } from "lucide-react";

import { AppIcon } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";

// iOS form rows: the label on the left, a borderless field filling the rest, hairlines between rows.
const FIELD_ROW =
  "relative flex min-h-12 items-center gap-3 px-4 not-first:before:absolute not-first:before:top-0 not-first:before:right-0 not-first:before:left-4 not-first:before:h-px not-first:before:bg-border focus-within:bg-primary/[0.03]";
const FIELD_LABEL = "w-24 shrink-0 text-[17px] sm:text-[15px]";
const FIELD_INPUT = "h-12 min-w-0 flex-1 bg-transparent text-[17px] outline-none placeholder:text-tertiary-foreground sm:text-[15px]";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const { login, register } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const isRegister = mode === "register";

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const email = String(form.get("email"));
    const password = String(form.get("password"));
    setBusy(true);
    setError(null);
    try {
      const user = isRegister
        ? await register(email, password, String(form.get("company")))
        : await login(email, password);
      router.push(user.company.assessed_at ? "/dashboard" : "/onboarding");
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <Link href="/" className="mx-auto mb-6 block w-fit" aria-label="ComIntern home">
          <AppIcon className="size-16 rounded-[16px]" />
        </Link>
        <h1 className="text-center text-[28px] font-bold tracking-tight">{isRegister ? "Create Account" : "Sign In"}</h1>
        <p className="mt-1 text-center text-[15px] text-muted-foreground">
          {isRegister ? "Start your compliance assessment in minutes." : "Welcome back to ComIntern."}
        </p>

        <form onSubmit={onSubmit} className="mt-8">
          <div className="overflow-hidden rounded-xl bg-card">
            {isRegister && (
              <div className={FIELD_ROW}>
                <label htmlFor="company" className={FIELD_LABEL}>
                  Company
                </label>
                <input id="company" name="company" required placeholder="Acme GmbH" autoComplete="organization" className={FIELD_INPUT} />
              </div>
            )}
            <div className={FIELD_ROW}>
              <label htmlFor="email" className={FIELD_LABEL}>
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                autoComplete="email"
                placeholder="name@company.com"
                className={FIELD_INPUT}
              />
            </div>
            <div className={FIELD_ROW}>
              <label htmlFor="password" className={FIELD_LABEL}>
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                minLength={8}
                autoComplete={isRegister ? "new-password" : "current-password"}
                placeholder={isRegister ? "At least 8 characters" : "Required"}
                className={FIELD_INPUT}
              />
            </div>
          </div>
          {error && (
            <p role="alert" className="mt-2 px-4 text-[13px] text-red-ink">
              {error}
            </p>
          )}
          <Button type="submit" size="lg" disabled={busy} className="mt-6 w-full">
            {busy && <Loader2 className="animate-spin" />}
            {isRegister ? "Create Account" : "Sign In"}
          </Button>
        </form>

        <p className="mt-6 text-center text-[15px] text-muted-foreground">
          {isRegister ? "Already have an account? " : "New to ComIntern? "}
          <Link href={isRegister ? "/login" : "/register"} className="text-primary hover:opacity-70">
            {isRegister ? "Sign In" : "Create Account"}
          </Link>
        </p>
      </div>
    </div>
  );
}
