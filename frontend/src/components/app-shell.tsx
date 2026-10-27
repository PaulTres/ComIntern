"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Bell,
  Bot,
  FileText,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Menu,
  Settings,
  X,
} from "lucide-react";

import { Logo } from "@/components/logo";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/regulations", label: "Regulations", icon: ListChecks },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/updates", label: "Updates", icon: Bell },
  { href: "/assistant", label: "Assistant", icon: Bot },
  { href: "/settings", label: "Company profile", icon: Settings },
];

/** Redirects to /login when signed out; renders nothing until the session is known. */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);
  if (loading || !user) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="size-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }
  return <>{children}</>;
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-1">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              active ? "bg-primary/10 font-medium text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="size-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

function UserBox() {
  const { user, logout } = useAuth();
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card p-3">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
        {user?.company.name.slice(0, 1).toUpperCase()}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{user?.company.name}</p>
        <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
      </div>
      <button onClick={logout} className="text-muted-foreground hover:text-foreground" aria-label="Sign out">
        <LogOut className="size-4" />
      </button>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex min-h-screen w-full">
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col gap-8 border-r bg-card/60 p-4 lg:flex">
        <div className="px-2 pt-1">
          <Logo href="/dashboard" />
        </div>
        <NavLinks />
        <div className="mt-auto">
          <UserBox />
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b bg-background/80 px-4 py-3 backdrop-blur lg:hidden">
          <Logo href="/dashboard" />
          <button onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu className="size-5" />
          </button>
        </header>
        {open && (
          <div className="fixed inset-0 z-40 lg:hidden">
            <div className="absolute inset-0 bg-black/30" onClick={() => setOpen(false)} />
            <div className="absolute inset-y-0 left-0 flex w-72 flex-col gap-6 bg-background p-4 shadow-xl">
              <div className="flex items-center justify-between px-2">
                <Logo href="/dashboard" />
                <button onClick={() => setOpen(false)} aria-label="Close menu">
                  <X className="size-5" />
                </button>
              </div>
              <NavLinks onNavigate={() => setOpen(false)} />
              <div className="mt-auto">
                <UserBox />
              </div>
            </div>
          </div>
        )}
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-8 sm:py-10">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  );
}
