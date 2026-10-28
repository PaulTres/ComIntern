"use client";

import { useState } from "react";

import { PageHeader } from "@/components/app-shell";
import { EmptyState, Loading, Section } from "@/components/list";
import { Switch } from "@/components/ui/switch";
import { UpdateItem } from "@/components/update-item";
import type { RegulatoryUpdate } from "@/lib/types";
import { useApi } from "@/lib/use-api";

export default function UpdatesPage() {
  const [relevantOnly, setRelevantOnly] = useState(true);
  const { data } = useApi<RegulatoryUpdate[]>(`/updates?relevant_only=${relevantOnly}`);

  return (
    <>
      <PageHeader
        title="Updates"
        description="New deadlines, amendments and guidance, curated by hand. Always check the official source."
      />

      <Section className="mb-8">
        <label className="flex min-h-12 cursor-pointer items-center justify-between gap-4 px-4 py-2">
          <span className="text-[17px] sm:text-[15px]">Only my regulations</span>
          <Switch checked={relevantOnly} onCheckedChange={setRelevantOnly} />
        </label>
      </Section>

      {!data ? (
        <Loading />
      ) : data.length === 0 ? (
        <EmptyState>No updates.</EmptyState>
      ) : (
        <div className="flex flex-col gap-3">
          {data.map((u) => (
            <div key={u.id} className="rounded-xl bg-card p-4 sm:p-5">
              <UpdateItem update={u} />
              {!u.relevant && <p className="mt-3 text-[13px] text-tertiary-foreground">Not one of your regulations.</p>}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
