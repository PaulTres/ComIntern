import { ChevronsUpDown } from "lucide-react";

import { cn } from "@/lib/utils";

/** The iOS segmented control: a gray track with the chosen segment raised. Scrolls sideways when it does not fit. */
export function SegmentedControl<T extends string | number | boolean>({
  options,
  value,
  onChange,
  label,
  className,
}: {
  options: { value: T; label: React.ReactNode }[];
  value: T | undefined;
  onChange: (value: T) => void;
  label: string;
  className?: string;
}) {
  return (
    <div className={cn("max-w-full overflow-x-auto [scrollbar-width:none]", className)}>
      <div role="radiogroup" aria-label={label} className="flex min-w-full rounded-[9px] bg-muted p-0.5">
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <button
              key={String(option.value)}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(option.value)}
              className={cn(
                "flex-1 rounded-[7px] px-3 py-1.5 text-[13px] font-medium whitespace-nowrap transition-all outline-none focus-visible:ring-2 focus-visible:ring-ring/50",
                selected
                  ? "bg-card shadow-[0_3px_8px_rgb(0_0_0/0.12),0_3px_1px_rgb(0_0_0/0.04)] dark:bg-[#636366]"
                  : "text-foreground/80 hover:text-foreground",
              )}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/** A native select styled as an Apple pop-up button: the platform picker opens on phones. */
export function Select({
  value,
  onChange,
  options,
  label,
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  label: string;
  className?: string;
}) {
  return (
    <div className={cn("relative inline-flex", className)}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={label}
        className="h-9 w-full cursor-pointer appearance-none rounded-full bg-muted py-0 pr-8 pl-3.5 text-[15px] font-medium outline-none hover:bg-foreground/10 focus-visible:ring-3 focus-visible:ring-ring/50"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <ChevronsUpDown className="pointer-events-none absolute top-1/2 right-3 size-3.5 -translate-y-1/2 text-muted-foreground" />
    </div>
  );
}
