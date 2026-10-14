"use client";

import Link from "next/link";
import { ArrowRight, FileText, Loader2 } from "lucide-react";

import { PageHeader } from "@/components/app-shell";
import { JurisdictionBadge, StatusBadge } from "@/components/badges";
import { LevelLabel, ScoreBar, ScoreRing } from "@/components/score";
import { EmptyState, SectionCard } from "@/components/section-card";
import { StatusBreakdown } from "@/components/status-breakdown";
import { buttonVariants } from "@/components/ui/button";
import { UpdateItem } from "@/components/update-item";
import { formatDate } from "@/lib/format";
import type { Dashboard } from "@/lib/types";
import { useApi } from "@/lib/use-api";

export default function DashboardPage() {
  const { data, error } = useApi<Dashboard>("/dashboard");

  if (error) return <EmptyState>Could not load the dashboard: {error.message}</EmptyState>;
  if (!data)
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );

  if (!data.assessed)
    return (
      <div className="mx-auto max-w-lg py-20 text-center">
        <h1 className="text-2xl font-semibold tracking-tight">Welcome to ComIntern</h1>
        <p className="mt-2 text-muted-foreground">
          Answer a few questions about {data.company_name} to find out which regulations apply to you.
        </p>
        <Link href="/onboarding" className={`${buttonVariants()} mt-6 h-10 px-4`}>
          Start assessment <ArrowRight />
        </Link>
      </div>
    );

  const { totals } = data;
  const applicable = totals.total - totals.not_applicable;

  return (
    <>
      <PageHeader title={`Good to see you, ${data.company_name}`} description="Your compliance readiness at a glance." />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <section className="flex flex-col items-center gap-6 rounded-xl border bg-card p-6 sm:flex-row lg:col-span-2">
          <ScoreRing score={data.overall_score} level={data.level} />
          <div className="flex-1 text-center sm:text-left">
            <p className="text-sm text-muted-foreground">Overall compliance score</p>
            <p className="mt-1 text-lg font-medium text-balance">
              {totals.compliant} of {applicable} applicable requirements are met across {data.regulations.length}{" "}
              regulations.
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {totals.evidenced} requirement{totals.evidenced === 1 ? " has" : "s have"} supporting evidence uploaded.
              Scores weight each requirement by importance; &ldquo;in progress&rdquo; counts half.
            </p>
          </div>
        </section>

        <SectionCard title="Requirement status">
          <StatusBreakdown score={totals} />
        </SectionCard>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <SectionCard title="Regulations" href="/regulations" className="lg:col-span-2">
          <ul className="-mx-2 flex flex-col">
            {data.regulations.map((r) => (
              <li key={r.code}>
                <Link
                  href={`/regulations/${r.code}`}
                  className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1 rounded-lg px-2 py-3 hover:bg-muted/60 sm:grid-cols-[minmax(0,14rem)_1fr]"
                >
                  <div className="flex min-w-0 items-center gap-2">
                    <span className="truncate text-sm font-medium">{r.short_name}</span>
                    <JurisdictionBadge code={r.jurisdiction} />
                  </div>
                  <LevelLabel level={r.score.level} className="justify-self-end sm:hidden" />
                  <ScoreBar score={r.score.score} level={r.score.level} className="col-span-2 sm:col-span-1" />
                </Link>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard title="Regulatory updates" href="/updates">
          {data.updates.length ? (
            <div className="flex flex-col gap-5">
              {data.updates.map((u) => (
                <UpdateItem key={u.id} update={u} compact />
              ))}
            </div>
          ) : (
            <EmptyState>No updates for your regulations.</EmptyState>
          )}
        </SectionCard>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <SectionCard title="Next steps" href="/regulations" linkLabel="All requirements">
          {data.open_tasks.length ? (
            <ul className="-mx-2 flex flex-col">
              {data.open_tasks.map((t) => (
                <li key={t.requirement_id}>
                  <Link
                    href={`/regulations/${t.regulation_code}#req-${t.requirement_id}`}
                    className="flex items-center gap-3 rounded-lg px-2 py-2.5 hover:bg-muted/60"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm">{t.title}</p>
                      <p className="text-xs text-muted-foreground">{t.regulation_short_name}</p>
                    </div>
                    <StatusBadge status={t.status} />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState>All requirements are handled. Great work!</EmptyState>
          )}
        </SectionCard>

        <SectionCard title="Recent evidence" href="/documents">
          {data.recent_documents.length ? (
            <ul className="flex flex-col gap-3">
              {data.recent_documents.map((d) => (
                <li key={d.id} className="flex items-center gap-3">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                    <FileText className="size-4 text-muted-foreground" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm">{d.filename}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {d.regulation_short_name ? `${d.regulation_short_name} · ${d.requirement_title}` : "Unassigned"}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground">{formatDate(d.uploaded_at)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState>Upload documents on a regulation&rsquo;s page to prove compliance.</EmptyState>
          )}
        </SectionCard>
      </div>
    </>
  );
}
