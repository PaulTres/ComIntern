import { CalendarClock, ExternalLink } from "lucide-react";

import { SeverityBadge } from "@/components/badges";
import { formatDate } from "@/lib/format";
import type { RegulatoryUpdate } from "@/lib/types";

export function UpdateItem({ update, compact = false }: { update: RegulatoryUpdate; compact?: boolean }) {
  return (
    <article className="flex flex-col gap-1.5">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <SeverityBadge severity={update.severity} />
        <span className="capitalize">{update.kind}</span>
        <span>·</span>
        <time>{formatDate(update.published_on)}</time>
      </div>
      <h3 className="text-sm font-medium leading-snug">{update.title}</h3>
      {!compact && <p className="text-sm text-muted-foreground">{update.summary}</p>}
      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        {update.effective_on && (
          <span className="inline-flex items-center gap-1">
            <CalendarClock className="size-3.5" /> Effective {formatDate(update.effective_on)}
          </span>
        )}
        {!compact && update.source_url && (
          <a href={update.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-primary hover:underline">
            Source <ExternalLink className="size-3" />
          </a>
        )}
      </div>
    </article>
  );
}
