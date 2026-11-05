"use client";

import Link from "next/link";
import { ClipboardList, FileText } from "lucide-react";

import { PageHeader } from "@/components/app-shell";
import { StatusBadge } from "@/components/badges";
import { EmptyState, IconTile, Loading, Row, RowText, Section, SeeAll } from "@/components/list";
import { LevelLabel, ScoreBar, ScoreRing } from "@/components/score";
import { StatusBreakdown } from "@/components/status-breakdown";
import { buttonVariants } from "@/components/ui/button";
import { UpdateItem } from "@/components/update-item";
import { formatDate } from "@/lib/format";
import type { Dashboard } from "@/lib/types";
import { useApi } from "@/lib/use-api";

export default function DashboardPage() {
  const { data, error } = useApi<Dashboard>("/dashboard");

  if (error) return <EmptyState>Could not load the dashboard: {error.message}</EmptyState>;
  if (!data) return <Loading />;

  if (!data.assessed)
    return (
      <>
        <PageHeader title={data.company_name} />
        <div className="mx-auto flex max-w-md flex-col items-center rounded-2xl bg-card px-6 py-12 text-center">
          <IconTile icon={ClipboardList} className="size-14 rounded-[14px] [&_svg]:size-7" />
          <h2 className="mt-5 text-[22px] font-bold tracking-tight">Start your assessment</h2>
          <p className="mt-2 text-[15px] text-muted-foreground">
            Answer a few questions about {data.company_name} to find out which regulations apply to you.
          </p>
          <Link href="/onboarding" className={buttonVariants({ size: "lg", className: "mt-6" })}>
            Start Assessment
          </Link>
        </div>
      </>
    );

  const { totals } = data;
  const applicable = totals.total - totals.not_applicable;

  return (
    <>
      <PageHeader title={data.company_name} description="Your compliance readiness at a glance." />

      <div className="grid grid-cols-1 gap-x-6 gap-y-8 lg:grid-cols-3">
        <Section title="Readiness" className="lg:col-span-2">
          <div className="flex flex-col items-center gap-6 p-6 sm:flex-row">
          <ScoreRing score={data.overall_score} level={data.level} />
          <div className="flex-1 text-center sm:text-left">
            <p className="text-[22px] leading-snug font-bold tracking-tight text-balance">
              {totals.compliant} of {applicable} requirements met across {data.regulations.length} regulations
            </p>
            <p className="mt-2 text-[15px] text-muted-foreground">
              {totals.evidenced} {totals.evidenced === 1 ? "requirement has" : "requirements have"} evidence. Each
              requirement counts by its priority; one in progress counts half.
            </p>
          </div>
          </div>
        </Section>

        <Section title="Status">
          <StatusBreakdown score={totals} />
        </Section>

        <Section title="Regulations" action={<SeeAll href="/regulations" />} className="lg:col-span-2">
          {data.regulations.map((r) => (
            <Row key={r.code} href={`/regulations/${r.code}`}>
              <RowText
                title={<span className="font-semibold">{r.short_name}</span>}
                subtitle={<LevelLabel level={r.score.level} />}
                className="sm:max-w-56"
              />
              <ScoreBar score={r.score.score} level={r.score.level} className="ml-auto w-28 sm:w-auto sm:flex-1" />
            </Row>
          ))}
        </Section>

        <Section title="Updates" action={<SeeAll href="/updates" />}>
          {data.updates.length ? (
            data.updates.map((u) => (
              <Row key={u.id} href="/updates" chevron={false} className="py-3">
                <UpdateItem update={u} compact />
              </Row>
            ))
          ) : (
            <p className="px-4 py-8 text-center text-[15px] text-muted-foreground">No updates for your regulations.</p>
          )}
        </Section>

        <Section title="Next Steps" className="lg:col-span-2">
          {data.open_tasks.length ? (
            data.open_tasks.map((t) => (
              <Row key={t.requirement_id} href={`/regulations/${t.regulation_code}#req-${t.requirement_id}`}>
                <RowText title={t.title} subtitle={t.regulation_short_name} />
                <StatusBadge status={t.status} />
              </Row>
            ))
          ) : (
            <p className="px-4 py-8 text-center text-[15px] text-muted-foreground">
              Every requirement is handled. Well done.
            </p>
          )}
        </Section>

        <Section title="Recent Evidence" action={<SeeAll href="/documents" />}>
          {data.recent_documents.length ? (
            data.recent_documents.map((d) => (
              <Row key={d.id} icon={<IconTile icon={FileText} className="bg-[#8e8e93]" />}>
                <RowText
                  title={d.filename}
                  subtitle={d.regulation_short_name ? `${d.regulation_short_name} · ${formatDate(d.uploaded_at)}` : formatDate(d.uploaded_at)}
                />
              </Row>
            ))
          ) : (
            <p className="px-4 py-8 text-center text-[15px] text-muted-foreground">
              Add documents on a regulation&rsquo;s page to prove each requirement.
            </p>
          )}
        </Section>
      </div>
    </>
  );
}
