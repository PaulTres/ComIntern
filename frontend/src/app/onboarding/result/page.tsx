"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2, Loader2, PencilLine } from "lucide-react";

import { JurisdictionBadge } from "@/components/badges";
import { Logo } from "@/components/logo";
import { buttonVariants } from "@/components/ui/button";
import type { RegulationSummary } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { cn } from "@/lib/utils";

const GROUPS = [
  { code: "EU", title: "European Union" },
  { code: "DE", title: "Germany" },
  { code: "RO", title: "Romania" },
];

export default function ResultPage() {
  const { data: regs } = useApi<RegulationSummary[]>("/company/regulations");

  return (
    <div className="flex flex-1 flex-col">
      <header className="mx-auto flex w-full max-w-4xl items-center px-4 py-5 sm:px-8">
        <Logo href="/dashboard" />
      </header>
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 pb-20 sm:px-8">
        {!regs ? (
          <div className="flex justify-center py-20">
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="animate-in fade-in duration-500">
            <div className="py-10 text-center">
              <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                <CheckCircle2 className="size-6" />
              </span>
              <h1 className="mt-5 text-3xl font-semibold tracking-tight">
                {regs.length === 0
                  ? "No regulations matched your profile"
                  : `${regs.length} regulation${regs.length === 1 ? "" : "s"} apply to you`}
              </h1>
              <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
                Based on your answers, these are the regulations you should prepare for. Each one comes with a
                checklist of requirements you can work through and attach evidence to.
              </p>
            </div>

            {GROUPS.map((g) => {
              const items = regs.filter((r) => r.jurisdiction === g.code);
              if (!items.length) return null;
              return (
                <section key={g.code} className="mb-10">
                  <h2 className="mb-3 text-sm font-medium tracking-wide text-muted-foreground uppercase">{g.title}</h2>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {items.map((r, i) => (
                      <div
                        key={r.code}
                        className="animate-in fade-in slide-in-from-bottom-2 fill-mode-both rounded-xl border bg-card p-5"
                        style={{ animationDelay: `${i * 60}ms` }}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h3 className="font-semibold">{r.short_name}</h3>
                            <p className="text-xs text-muted-foreground">{r.category}</p>
                          </div>
                          <JurisdictionBadge code={r.jurisdiction} />
                        </div>
                        <ul className="mt-3 flex flex-col gap-1.5">
                          {r.reasons.map((reason) => (
                            <li key={reason} className="flex gap-2 text-sm text-muted-foreground">
                              <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                              {reason}
                            </li>
                          ))}
                        </ul>
                        <p className="mt-3 text-xs text-muted-foreground">{r.score.total} requirements</p>
                      </div>
                    ))}
                  </div>
                </section>
              );
            })}

            <div className="flex flex-col-reverse items-center justify-center gap-3 sm:flex-row">
              <Link href="/onboarding" className={cn(buttonVariants({ variant: "outline" }), "h-10")}>
                <PencilLine /> Edit answers
              </Link>
              <Link href="/dashboard" className={cn(buttonVariants(), "h-10 px-4")}>
                Go to my dashboard <ArrowRight />
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
