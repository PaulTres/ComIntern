import { cn } from "@/lib/utils";
import { AlertTriangle, CheckCircle2, CircleDashed, XCircle } from "lucide-react";

import { LEVEL_BG, LEVEL_LABEL, LEVEL_STROKE, LEVEL_TEXT } from "@/lib/format";
import type { Level } from "@/lib/types";

export function ScoreRing({
  score,
  level,
  size = 168,
  stroke = 14,
  showLabel = true,
}: {
  score: number | null;
  level: Level;
  size?: number;
  stroke?: number;
  showLabel?: boolean;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - (score ?? 0) / 100);
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth={stroke} className="stroke-muted" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className={cn("transition-[stroke-dashoffset] duration-700 ease-out", LEVEL_STROKE[level])}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-semibold tabular-nums" style={{ fontSize: size / 4.2 }}>
          {score ?? "–"}
          {score !== null && <span className="text-[0.45em] text-muted-foreground">%</span>}
        </span>
        {showLabel && <LevelLabel level={level} />}
      </div>
    </div>
  );
}

export function ScoreBar({ score, level, className }: { score: number | null; level: Level; className?: string }) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full transition-[width] duration-700 ease-out", LEVEL_BG[level])}
          style={{ width: `${score ?? 0}%` }}
        />
      </div>
      <span className="w-10 text-right text-sm font-medium tabular-nums">
        {score ?? "–"}
        {score !== null && "%"}
      </span>
    </div>
  );
}

const LEVEL_ICON = { green: CheckCircle2, amber: AlertTriangle, red: XCircle, none: CircleDashed };

/** Status is never color-only: icon + text label. */
export function LevelLabel({ level, className }: { level: Level; className?: string }) {
  const Icon = LEVEL_ICON[level];
  return (
    <span className={cn("inline-flex items-center gap-1 text-xs font-medium", LEVEL_TEXT[level], className)}>
      <Icon className="size-3.5" />
      {LEVEL_LABEL[level]}
    </span>
  );
}
