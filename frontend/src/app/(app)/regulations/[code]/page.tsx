"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Bot, ExternalLink, Landmark, Loader2 } from "lucide-react";

import { JurisdictionBadge } from "@/components/badges";
import { RequirementCard } from "@/components/requirement-card";
import { ScoreRing } from "@/components/score";
import { EmptyState, SectionCard } from "@/components/section-card";
import { StatusBreakdown } from "@/components/status-breakdown";
import { UpdateItem } from "@/components/update-item";
import type { RegulationDetail, Requirement } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { cn } from "@/lib/utils";

const FILTERS: { label: string; match: (r: Requirement) => boolean }[] = [
  { label: "All", match: () => true },
  { label: "Open", match: (r) => r.status === "not_started" || r.status === "in_progress" },
  { label: "Compliant", match: (r) => r.status === "compliant" },
  { label: "Missing evidence", match: (r) => r.status !== "not_applicable" && r.documents.length === 0 },
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
  if (!reg)
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );

  const visible = reg.requirements.filter(FILTERS[filter].match);

  return (
    <>
      <Link href="/regulations" className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" /> All regulations
      </Link>

      <div className="flex flex-col gap-6 rounded-xl border bg-card p-6 sm:flex-row sm:items-center">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <JurisdictionBadge code={reg.jurisdiction} />
            <span className="text-xs text-muted-foreground">{reg.category}</span>
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">{reg.short_name}</h1>
          <p className="text-sm text-muted-foreground">{reg.name}</p>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed">{reg.summary}</p>
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground">
            {reg.authority && (
              <span className="inline-flex items-center gap-1.5">
                <Landmark className="size-3.5" /> {reg.authority}
              </span>
            )}
            {reg.source_url && (
              <a href={reg.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-primary hover:underline">
                Official source <ExternalLink className="size-3" />
              </a>
            )}
            <Link href={`/assistant?regulation=${reg.code}`} className="inline-flex items-center gap-1 text-primary hover:underline">
              <Bot className="size-3.5" /> Ask the {reg.short_name} agent
            </Link>
          </div>
        </div>
        <div className="flex justify-center">
          <ScoreRing score={reg.score.score} level={reg.score.level} size={136} stroke={12} />
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="flex flex-col gap-4 lg:col-span-2">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="font-medium">Requirements</h2>
            <div className="flex flex-wrap gap-1 rounded-lg border bg-card p-1">
              {FILTERS.map((f, i) => (
                <button
                  key={f.label}
                  onClick={() => setFilter(i)}
                  className={cn(
                    "rounded-md px-2.5 py-1 text-xs transition-colors",
                    filter === i ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {f.label} <span className="opacity-70">{reg.requirements.filter(f.match).length}</span>
                </button>
              ))}
            </div>
          </div>
          {visible.length ? (
            visible.map((r) => (
              <RequirementCard key={r.id} requirement={r} onChanged={reload} defaultOpen={hash === `#req-${r.id}`} />
            ))
          ) : (
            <EmptyState>No requirements in this view.</EmptyState>
          )}
        </div>

        <div className="flex flex-col gap-4">
          <SectionCard title="Why this applies">
            <ul className="flex flex-col gap-2">
              {reg.reasons.map((reason) => (
                <li key={reason} className="flex gap-2 text-sm text-muted-foreground">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                  {reason}
                </li>
              ))}
            </ul>
          </SectionCard>
          <SectionCard title="Progress">
            <StatusBreakdown score={reg.score} />
          </SectionCard>
          <SectionCard title="Updates">
            {reg.updates.length ? (
              <div className="flex flex-col gap-5">
                {reg.updates.map((u) => (
                  <UpdateItem key={u.id} update={u} />
                ))}
              </div>
            ) : (
              <EmptyState>No recent updates.</EmptyState>
            )}
          </SectionCard>
        </div>
      </div>
    </>
  );
}
