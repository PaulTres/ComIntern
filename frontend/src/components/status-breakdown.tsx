import type { Score } from "@/lib/types";

const SEGMENTS = [
  { key: "compliant", label: "Compliant", color: "bg-emerald-500" },
  { key: "in_progress", label: "In progress", color: "bg-amber-400" },
  { key: "not_started", label: "Not started", color: "bg-slate-300" },
  { key: "not_applicable", label: "Not applicable", color: "bg-slate-200 bg-[repeating-linear-gradient(45deg,transparent_0_3px,rgb(255_255_255/0.7)_3px_5px)]" },
] as const;

/** Single stacked bar of requirement statuses with legend; segments separated by 2px gaps. */
export function StatusBreakdown({ score }: { score: Score }) {
  const total = score.total || 1;
  return (
    <div>
      <div className="flex h-3 w-full gap-0.5 overflow-hidden rounded-full bg-muted">
        {SEGMENTS.map(({ key, label, color }) => {
          const n = score[key];
          if (!n) return null;
          return (
            <div
              key={key}
              title={`${label}: ${n} of ${score.total}`}
              className={`${color} h-full transition-[width] duration-700 first:rounded-l-full last:rounded-r-full hover:opacity-80`}
              style={{ width: `${(n / total) * 100}%` }}
            />
          );
        })}
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2">
        {SEGMENTS.map(({ key, label, color }) => (
          <div key={key} className="flex items-center gap-2 text-sm">
            <span className={`size-2.5 shrink-0 rounded-sm ${color}`} />
            <dt className="text-muted-foreground">{label}</dt>
            <dd className="ml-auto font-medium tabular-nums">{score[key]}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
