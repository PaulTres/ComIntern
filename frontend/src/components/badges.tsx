import { cn } from "@/lib/utils";
import { STATUS_LABEL } from "@/lib/format";
import type { RegulatoryUpdate, Status } from "@/lib/types";

const pill = "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap";

const STATUS_STYLE: Record<Status, string> = {
  not_started: "bg-muted text-muted-foreground",
  in_progress: "bg-amber-100 text-amber-800",
  compliant: "bg-emerald-100 text-emerald-800",
  not_applicable: "bg-slate-100 text-slate-500 line-through decoration-slate-400/60",
};

export function StatusBadge({ status }: { status: Status }) {
  return <span className={cn(pill, STATUS_STYLE[status])}>{STATUS_LABEL[status]}</span>;
}

const JURISDICTION: Record<string, { label: string; style: string }> = {
  EU: { label: "EU", style: "bg-blue-100 text-blue-800" },
  DE: { label: "Germany", style: "bg-zinc-900 text-amber-300" },
  RO: { label: "Romania", style: "bg-yellow-100 text-blue-900" },
};

export function JurisdictionBadge({ code }: { code: string }) {
  const j = JURISDICTION[code] ?? { label: code, style: "bg-muted" };
  return <span className={cn(pill, j.style)}>{j.label}</span>;
}

const SEVERITY: Record<RegulatoryUpdate["severity"], string> = {
  info: "bg-sky-100 text-sky-800",
  important: "bg-amber-100 text-amber-800",
  critical: "bg-rose-100 text-rose-800",
};

export function SeverityBadge({ severity }: { severity: RegulatoryUpdate["severity"] }) {
  return <span className={cn(pill, SEVERITY[severity], "capitalize")}>{severity}</span>;
}
