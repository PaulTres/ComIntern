"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowUpRight, Check, MessageCircle } from "lucide-react";

import { PageHeader } from "@/components/app-shell";
import { JurisdictionBadge } from "@/components/badges";
import { SegmentedControl } from "@/components/controls";
import { EmptyState, Loading, Row, Section } from "@/components/list";
import { RequirementCard } from "@/components/requirement-card";
import { ScoreRing } from "@/components/score";
import { StatusBreakdown } from "@/components/status-breakdown";
import { buttonVariants } from "@/components/ui/button";
import { UpdateItem } from "@/components/update-item";
import type { RegulationDetail, Requirement } from "@/lib/types";
import { useApi } from "@/lib/use-api";

const FILTERS: { label: string; match: (r: Requirement) => boolean }[] = [
  { label: "All", match: () => true },
  { label: "Open", match: (r) => r.status === "not_started" || r.status === "in_progress" },
  { label: "Compliant", match: (r) => r.status === "compliant" },
  { label: "No evidence", match: (r) => r.status !== "not_applicable" && r.documents.length === 0 },
];

export default function RegulationDetailPage() {
  const { code } = useParams<{ code: string }>();
  const { data: reg, error, reload } = useApi<RegulationDetail>(`/regulations/${code}`);
  const [filter, setFilter] = useState(0);
  const [hash] = useState(() => (typeof window === "undefined" ? "" : window.location.hash));

  useEffect(() => {
    if (reg && hash) document.querySelector(hash)?.scrollIntoView({ behavior: "smooth" });
  }, [reg, hash]);

  if (error) return <EmptyState>{error.message}</EmptyState>;
  if (!reg) return <Loading />;

  const visible = reg.requirements.filter(FILTERS[filter].match);

  return (
    <>
      <PageHeader title={reg.short_name} description={reg.name} back={{ href: "/regulations", label: "Regulations" }} />

      <div className="flex flex-col-reverse gap-6 rounded-xl bg-card p-5 sm:flex-row sm:items-center sm:p-6">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-[13px] text-muted-foreground">
            <JurisdictionBadge code={reg.jurisdiction} />
            <span>{reg.category}</span>
            {reg.authority && (
              <>
                <span aria-hidden>·</span>
                <span>{reg.authority}</span>
              </>
            )}
          </div>
          <p className="mt-3 max-w-2xl text-[15px] leading-relaxed">{reg.summary}</p>
          <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2">
            <Link href={`/assistant?regulation=${reg.code}`} className={buttonVariants({ variant: "tinted" })}>
              <MessageCircle /> Ask the {reg.short_name} Agent
            </Link>
            {reg.source_url && (
              <a href={reg.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-[15px] text-primary hover:opacity-70">
                Official source <ArrowUpRight className="size-4" />
              </a>
            )}
          </div>
        </div>
        <div className="flex justify-center">
          <ScoreRing score={reg.score.score} level={reg.score.level} size={140} stroke={14} />
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-x-6 gap-y-8 lg:grid-cols-3">
        <section className="flex flex-col gap-3 lg:col-span-2">
          <div className="flex flex-col gap-3 px-1 sm:flex-row sm:items-end sm:justify-between">
            <h2 className="text-[20px] leading-tight font-semibold tracking-tight">Requirements</h2>
            <SegmentedControl
              label="Show requirements"
              value={filter}
              onChange={setFilter}
              options={FILTERS.map((f, i) => ({
                value: i,
                label: (
                  <>
                    {f.label} <span className="text-muted-foreground tabular-nums">{reg.requirements.filter(f.match).length}</span>
                  </>
                ),
              }))}
            />
          </div>
          {visible.length ? (
            visible.map((r) => (
              <RequirementCard key={r.id} requirement={r} onChanged={reload} defaultOpen={hash === `#req-${r.id}`} />
            ))
          ) : (
            <EmptyState>No requirements in this view.</EmptyState>
          )}
        </section>

        <div className="flex flex-col gap-8">
          <Section title="Why This Applies">
            {reg.reasons.map((reason) => (
              <Row key={reason} className="items-start">
                <Check className="mt-0.5 size-4 shrink-0 text-green" strokeWidth={2.5} />
                <span className="text-[15px] leading-snug">{reason}</span>
              </Row>
            ))}
          </Section>
          <Section title="Progress">
            <StatusBreakdown score={reg.score} />
          </Section>
          <Section title="Updates">
            {reg.updates.length ? (
              reg.updates.map((u) => (
                <Row key={u.id} className="py-3">
                  <UpdateItem update={u} />
                </Row>
              ))
            ) : (
              <p className="px-4 py-8 text-center text-[15px] text-muted-foreground">No recent updates.</p>
            )}
          </Section>
        </div>
      </div>
    </>
  );
}
