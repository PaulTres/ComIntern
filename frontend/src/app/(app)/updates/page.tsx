"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { PageHeader } from "@/components/app-shell";
import { EmptyState } from "@/components/section-card";
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
        title="Regulatory updates"
        description="New deadlines, amendments and guidance. Curated entries – always check the official source."
        action={
          <label className="flex items-center gap-2 text-sm">
            <Switch checked={relevantOnly} onCheckedChange={setRelevantOnly} />
            Only my regulations
          </label>
        }
      />
      {!data ? (
        <div className="flex justify-center py-20">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : data.length === 0 ? (
        <EmptyState>No updates.</EmptyState>
      ) : (
        <ol className="relative flex flex-col gap-4 border-l pl-6">
          {data.map((u) => (
            <li key={u.id} className="relative">
              <span
                className={`absolute top-6 -left-[1.95rem] size-3 rounded-full border-2 border-background ${u.relevant ? "bg-primary" : "bg-muted-foreground/40"}`}
              />
              <div className="rounded-xl border bg-card p-5">
                <UpdateItem update={u} />
                {!u.relevant && <p className="mt-3 text-xs text-muted-foreground">Not among your applicable regulations.</p>}
              </div>
            </li>
          ))}
        </ol>
      )}
    </>
  );
}
