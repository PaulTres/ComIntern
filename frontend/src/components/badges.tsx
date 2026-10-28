import { cn } from "@/lib/utils";
import { STATUS_LABEL } from "@/lib/format";
import type { RegulatoryUpdate, Status } from "@/lib/types";

const capsule = "inline-flex items-center rounded-full px-2 py-0.5 text-[12px] font-semibold whitespace-nowrap";

const STATUS_STYLE: Record<Status, string> = {
  not_started: "bg-muted text-muted-foreground",
  in_progress: "bg-orange/15 text-orange-ink",
  compliant: "bg-green/15 text-green-ink",
  not_applicable: "bg-muted text-tertiary-foreground",
};

export function StatusBadge({ status }: { status: Status }) {
  return <span className={cn(capsule, STATUS_STYLE[status])}>{STATUS_LABEL[status]}</span>;
}

export const JURISDICTION_LABEL: Record<string, string> = { EU: "European Union", DE: "Germany", RO: "Romania" };

export function JurisdictionBadge({ code }: { code: string }) {
  return <span className={cn(capsule, "bg-muted font-medium text-muted-foreground")}>{code === "EU" ? "EU" : JURISDICTION_LABEL[code] ?? code}</span>;
}

const SEVERITY: Record<RegulatoryUpdate["severity"], string> = {
  info: "bg-blue/12 text-blue",
  important: "bg-orange/15 text-orange-ink",
  critical: "bg-red/12 text-red-ink",
};

export function SeverityBadge({ severity }: { severity: RegulatoryUpdate["severity"] }) {
  return <span className={cn(capsule, SEVERITY[severity], "capitalize")}>{severity}</span>;
}
