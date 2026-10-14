"use client";

import Link from "next/link";
import { useState } from "react";
import { Loader2 } from "lucide-react";

import { PageHeader } from "@/components/app-shell";
import { JurisdictionBadge } from "@/components/badges";
import { LevelLabel, ScoreBar } from "@/components/score";
import { EmptyState } from "@/components/section-card";
import { buttonVariants } from "@/components/ui/button";
import type { RegulationSummary } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { cn } from "@/lib/utils";

const FILTERS = ["All", "EU", "DE", "RO"] as const;

export default function RegulationsPage() {
  const { data } = useApi<RegulationSummary[]>("/company/regulations");
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("All");
  const regs = data?.filter((r) => filter === "All" || r.jurisdiction === filter) ?? [];

  return (
    <>
      <PageHeader
        title="Regulations"
        description="Everything that applies to your company, based on your profile."
        action={
          <Link href="/onboarding" className={buttonVariants({ variant: "outline" })}>
            Re-run assessment
          </Link>
        }
      />
      <div className="mb-6 flex gap-1 rounded-lg border bg-card p-1 sm:w-fit">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "flex-1 rounded-md px-3 py-1.5 text-sm transition-colors sm:flex-none",
              filter === f ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {f === "All" ? "All" : f === "EU" ? "EU" : f === "DE" ? "Germany" : "Romania"}
          </button>
        ))}
      </div>

      {!data ? (
        <div className="flex justify-center py-20">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : regs.length === 0 ? (
        <EmptyState>No regulations in this view.</EmptyState>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {regs.map((r) => (
            <Link
              key={r.code}
              href={`/regulations/${r.code}`}
              className="group flex flex-col rounded-xl border bg-card p-5 transition-shadow hover:shadow-md"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="font-semibold group-hover:text-primary">{r.short_name}</h2>
                  <p className="truncate text-xs text-muted-foreground">{r.name}</p>
                </div>
                <JurisdictionBadge code={r.jurisdiction} />
              </div>
              <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">{r.summary}</p>
              <div className="mt-auto pt-5">
                <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {r.score.compliant}/{r.score.total - r.score.not_applicable} requirements met · {r.score.evidenced} evidenced
                  </span>
                  <LevelLabel level={r.score.level} />
                </div>
                <ScoreBar score={r.score.score} level={r.score.level} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
