"use client";

import Link from "next/link";
import { useState } from "react";
import { ChevronRight } from "lucide-react";

import { PageHeader } from "@/components/app-shell";
import { JurisdictionBadge } from "@/components/badges";
import { SegmentedControl } from "@/components/controls";
import { EmptyState, Loading } from "@/components/list";
import { LevelLabel, ScoreBar } from "@/components/score";
import { buttonVariants } from "@/components/ui/button";
import type { RegulationSummary } from "@/lib/types";
import { useApi } from "@/lib/use-api";

const FILTERS = [
  { value: "All", label: "All" },
  { value: "EU", label: "EU" },
  { value: "DE", label: "Germany" },
  { value: "RO", label: "Romania" },
];

export default function RegulationsPage() {
  const { data } = useApi<RegulationSummary[]>("/company/regulations");
  const [filter, setFilter] = useState("All");
  const regs = data?.filter((r) => filter === "All" || r.jurisdiction === filter) ?? [];

  return (
    <>
      <PageHeader
        title="Regulations"
        description="Everything that applies to your company, based on your answers."
        action={
          <Link href="/onboarding" className={buttonVariants({ variant: "tinted" })}>
            Re-run Assessment
          </Link>
        }
      />
      <SegmentedControl label="Jurisdiction" options={FILTERS} value={filter} onChange={setFilter} className="mb-6 sm:w-96" />

      {!data ? (
        <Loading />
      ) : regs.length === 0 ? (
        <EmptyState>No regulations in this view.</EmptyState>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {regs.map((r) => (
            <Link
              key={r.code}
              href={`/regulations/${r.code}`}
              className="group flex flex-col rounded-xl bg-card p-5 transition-shadow outline-none hover:shadow-[0_4px_20px_rgb(0_0_0/0.06)] focus-visible:ring-3 focus-visible:ring-ring/50 active:opacity-80"
            >
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h2 className="text-[17px] font-semibold">{r.short_name}</h2>
                    <JurisdictionBadge code={r.jurisdiction} />
                  </div>
                  <p className="mt-0.5 truncate text-[13px] text-muted-foreground">{r.name}</p>
                </div>
                <ChevronRight className="mt-1 size-4 shrink-0 text-tertiary-foreground transition-transform group-hover:translate-x-0.5" />
              </div>
              <p className="mt-3 line-clamp-2 text-[15px] leading-snug text-muted-foreground">{r.summary}</p>
              <div className="mt-auto pt-5">
                <div className="mb-2 flex items-center justify-between gap-2 text-[13px] text-muted-foreground">
                  <span>
                    {r.score.compliant} of {r.score.total - r.score.not_applicable} met · {r.score.evidenced} with evidence
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
