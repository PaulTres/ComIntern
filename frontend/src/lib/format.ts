import type { Condition, Level, Status } from "@/lib/types";

export const STATUS_LABEL: Record<Status, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  compliant: "Compliant",
  not_applicable: "Not applicable",
};

export const LEVEL_TEXT: Record<Level, string> = {
  green: "text-emerald-600",
  amber: "text-amber-600",
  red: "text-rose-600",
  none: "text-muted-foreground",
};

export const LEVEL_BG: Record<Level, string> = {
  green: "bg-emerald-500",
  amber: "bg-amber-500",
  red: "bg-rose-500",
  none: "bg-muted-foreground/30",
};

export const LEVEL_STROKE: Record<Level, string> = {
  green: "stroke-emerald-500",
  amber: "stroke-amber-500",
  red: "stroke-rose-500",
  none: "stroke-muted-foreground/30",
};

export const LEVEL_LABEL: Record<Level, string> = {
  green: "Audit-ready",
  amber: "Needs work",
  red: "At risk",
  none: "Not assessed",
};

export function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/** Mirrors backend services/applicability.evaluate for questionnaire `show_if`. */
export function isVisible(cond: Condition | undefined, answers: Record<string, unknown>): boolean {
  if (!cond?.field) return true;
  const actual = answers[cond.field];
  switch (cond.op ?? "eq") {
    case "eq":
      return actual === cond.value;
    case "in":
      return Array.isArray(cond.value) && cond.value.includes(actual);
    case "contains":
      return Array.isArray(actual) && actual.includes(cond.value);
    default:
      return true;
  }
}
