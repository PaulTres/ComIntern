import type { Score } from "@/lib/types";

const SEGMENTS = [
  { key: "compliant", label: "Compliant", color: "bg-green" },
  { key: "in_progress", label: "In progress", color: "bg-orange" },
  { key: "not_started", label: "Not started", color: "bg-foreground/20" },
  { key: "not_applicable", label: "Not applicable", color: "bg-foreground/8" },
] as const;

/** One stacked bar of requirement statuses, with the counts listed below it. */
export function StatusBreakdown({ score }: { score: Score }) {
  const total = score.total || 1;
  return (
    <div className="p-4">
      <div className="flex h-2 w-full gap-0.5 overflow-hidden rounded-full bg-muted">
        {SEGMENTS.map(({ key, label, color }) => {
          const n = score[key];
          if (!n) return null;
          return (
            <div
              key={key}
              title={`${label}: ${n} of ${score.total}`}
              className={`${color} h-full transition-[width] duration-700`}
              style={{ width: `${(n / total) * 100}%` }}
            />
          );
        })}
      </div>
      <dl className="mt-4 flex flex-col gap-2.5">
        {SEGMENTS.map(({ key, label, color }) => (
          <div key={key} className="flex items-center gap-2.5 text-[15px]">
            <span className={`size-2.5 shrink-0 rounded-full ${color}`} />
            <dt>{label}</dt>
            <dd className="ml-auto font-rounded font-semibold text-muted-foreground tabular-nums">{score[key]}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
