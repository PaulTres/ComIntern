import { ArrowUpRight } from "lucide-react";

import { SeverityBadge } from "@/components/badges";
import { formatDate } from "@/lib/format";
import type { RegulatoryUpdate } from "@/lib/types";

export function UpdateItem({ update, compact = false }: { update: RegulatoryUpdate; compact?: boolean }) {
  return (
    <article className="flex min-w-0 flex-1 flex-col gap-1">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[13px] text-muted-foreground">
        <SeverityBadge severity={update.severity} />
        <span className="capitalize">{update.kind}</span>
        <span aria-hidden>·</span>
        <time dateTime={update.published_on}>{formatDate(update.published_on)}</time>
      </div>
      <h3 className={compact ? "text-[15px] leading-snug" : "text-[17px] leading-snug font-semibold"}>{update.title}</h3>
      {!compact && <p className="text-[15px] leading-relaxed text-muted-foreground">{update.summary}</p>}
      {(update.effective_on || (!compact && update.source_url)) && (
        <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px]">
          {update.effective_on && (
            <span className="text-muted-foreground">Effective {formatDate(update.effective_on)}</span>
          )}
          {!compact && update.source_url && (
            <a href={update.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-primary hover:opacity-70">
              Official source <ArrowUpRight className="size-3.5" />
            </a>
          )}
        </div>
      )}
    </article>
  );
}
