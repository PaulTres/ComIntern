"use client";

import Link from "next/link";
import { Check } from "lucide-react";

import { JURISDICTION_LABEL } from "@/components/badges";
import { Loading, Row, RowText, Section } from "@/components/list";
import { buttonVariants } from "@/components/ui/button";
import type { RegulationSummary } from "@/lib/types";
import { useApi } from "@/lib/use-api";

export default function ResultPage() {
  const { data: regs } = useApi<RegulationSummary[]>("/company/regulations");

  if (!regs) return <Loading />;

  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-4 pt-16 pb-16 sm:px-6 sm:pt-20">
      <div className="animate-in fade-in duration-500 text-center">
        <span className="mx-auto flex size-16 items-center justify-center rounded-full bg-green text-white">
          <Check className="size-9" strokeWidth={2.5} />
        </span>
        <h1 className="mt-6 text-[28px] leading-tight font-bold tracking-tight sm:text-[34px]">
          {regs.length === 0
            ? "No regulations matched your profile"
            : `${regs.length} regulation${regs.length === 1 ? " applies" : "s apply"} to you`}
        </h1>
        <p className="mx-auto mt-3 max-w-lg text-[17px] text-muted-foreground">
          Each one comes with a checklist of requirements you can work through and attach evidence to.
        </p>
      </div>

      <div className="mt-10 flex flex-col gap-8">
        {["EU", "DE", "RO"].map((code) => {
          const items = regs.filter((r) => r.jurisdiction === code);
          if (!items.length) return null;
          return (
            <Section key={code} title={JURISDICTION_LABEL[code]}>
              {items.map((r) => (
                <Row key={r.code} href={`/regulations/${r.code}`}>
                  <RowText
                    title={<span className="font-semibold">{r.short_name}</span>}
                    subtitle={r.reasons[0] ?? r.category}
                  />
                  <span className="shrink-0 text-[13px] text-muted-foreground">{r.score.total} requirements</span>
                </Row>
              ))}
            </Section>
          );
        })}
      </div>

      <div className="mt-10 flex flex-col items-center gap-3">
        <Link href="/dashboard" className={buttonVariants({ size: "lg", className: "w-full sm:w-auto" })}>
          Go to My Dashboard
        </Link>
        <Link href="/onboarding" className={buttonVariants({ variant: "plain" })}>
          Edit Answers
        </Link>
      </div>
    </main>
  );
}
