"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Bell, Building2, ChevronLeft, Folder, LayoutGrid, LogOut, MessageCircle, ScrollText } from "lucide-react";

import { Loading } from "@/components/list";
import { Logo } from "@/components/logo";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

// The first five are the tab bar on phones; the company profile is reached from the avatar there.
const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutGrid },
  { href: "/regulations", label: "Regulations", icon: ScrollText },
  { href: "/documents", label: "Documents", icon: Folder },
  { href: "/assistant", label: "Assistant", icon: MessageCircle },
  { href: "/updates", label: "Updates", icon: Bell },
  { href: "/settings", label: "Company", icon: Building2 },
];

/** Redirects to /login when signed out; renders nothing until the session is known. */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);
  if (loading || !user) return <Loading />;
  return <>{children}</>;
}

function useIsActive() {
  const pathname = usePathname();
  return (href: string) => pathname === href || pathname.startsWith(`${href}/`);
}

function Sidebar() {
  const isActive = useIsActive();
  const { user, logout } = useAuth();
  return (
    <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col border-r bg-card/70 px-3 pt-5 pb-4 backdrop-blur-xl lg:flex">
      <div className="px-2.5 pb-6">
        <Logo href="/dashboard" />
      </div>
      <nav className="flex flex-col gap-0.5" aria-label="Main">
        {NAV.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={isActive(href) ? "page" : undefined}
            className={cn(
              "flex h-9 items-center gap-3 rounded-lg px-2.5 text-[15px] transition-colors",
              isActive(href) ? "bg-muted font-semibold" : "hover:bg-foreground/[0.04]",
            )}
          >
            <Icon className="size-[18px] text-primary" />
            {label}
          </Link>
        ))}
      </nav>
      <div className="mt-auto flex items-center gap-3 rounded-xl px-2.5 py-2">
        <Avatar name={user?.company.name ?? ""} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-semibold">{user?.company.name}</p>
          <p className="truncate text-[12px] text-muted-foreground">{user?.email}</p>
        </div>
        <button
          onClick={logout}
          className="flex size-8 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground"
          aria-label="Sign out"
          title="Sign out"
        >
          <LogOut className="size-4" />
        </button>
      </div>
    </aside>
  );
}

function TabBar() {
  const isActive = useIsActive();
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-40 border-t bg-card/80 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl lg:hidden"
    >
      <div className="mx-auto flex max-w-lg">
        {NAV.slice(0, 5).map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={isActive(href) ? "page" : undefined}
            className={cn(
              "flex h-[50px] flex-1 flex-col items-center justify-center gap-0.5 text-[10px] font-medium",
              isActive(href) ? "text-primary" : "text-muted-foreground",
            )}
          >
            <Icon className="size-6" strokeWidth={isActive(href) ? 2.2 : 1.8} />
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}

function Avatar({ name }: { name: string }) {
  return (
    <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-b from-[#a1a1a6] to-[#8e8e93] text-[13px] font-semibold text-white">
      {name.slice(0, 1).toUpperCase()}
    </span>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh w-full">
      <Sidebar />
      <main className="mx-auto w-full max-w-5xl min-w-0 flex-1 px-4 pt-6 pb-[calc(env(safe-area-inset-bottom)+6rem)] sm:px-6 lg:px-10 lg:pt-10 lg:pb-16">
        {children}
      </main>
      <TabBar />
    </div>
  );
}

/** A large title, as at the top of an iOS screen. On phones the avatar opens the company profile. */
export function PageHeader({
  title,
  description,
  action,
  back,
}: {
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  back?: { href: string; label: string };
}) {
  const { user } = useAuth();
  return (
    <header className="mb-6 sm:mb-8">
      <div className="flex min-h-8 items-center justify-between">
        {back ? (
          <Link href={back.href} className="-ml-1.5 inline-flex items-center text-[17px] text-primary hover:opacity-70">
            <ChevronLeft className="size-6" strokeWidth={2.2} /> {back.label}
          </Link>
        ) : (
          <span />
        )}
        <Link href="/settings" aria-label="Company profile" className="lg:hidden">
          <Avatar name={user?.company.name ?? ""} />
        </Link>
      </div>
      <div className="mt-1 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <h1 className="text-[28px] leading-tight font-bold tracking-tight text-balance sm:text-[34px]">{title}</h1>
          {description && <p className="mt-1 max-w-2xl text-[15px] text-muted-foreground">{description}</p>}
        </div>
        {action && <div className="flex shrink-0 flex-wrap items-center gap-2">{action}</div>}
      </div>
    </header>
  );
}
