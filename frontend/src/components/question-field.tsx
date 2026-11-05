"use client";

import { Check } from "lucide-react";

import { SegmentedControl } from "@/components/controls";
import { Input } from "@/components/ui/input";
import type { Question } from "@/lib/types";
import { cn } from "@/lib/utils";

/** A list row that shows a blue checkmark when chosen, as in iOS pickers. */
function Choice({ selected, onClick, children }: { selected: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className="relative flex min-h-11 w-full items-center gap-3 px-4 py-2.5 text-left text-[17px] transition-colors outline-none not-first:before:absolute not-first:before:top-0 not-first:before:right-0 not-first:before:left-4 not-first:before:h-px not-first:before:bg-border hover:bg-foreground/[0.03] focus-visible:bg-foreground/[0.05] active:bg-foreground/[0.08] sm:text-[15px]"
    >
      <span className="flex-1">{children}</span>
      <Check className={cn("size-5 shrink-0 text-primary", !selected && "invisible")} strokeWidth={2.5} />
    </button>
  );
}

export function QuestionField({
  question,
  value,
  onChange,
}: {
  question: Question;
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  const label = (
    <div className="mb-2 flex items-baseline justify-between gap-4 px-1">
      <p className="text-[17px] font-semibold">{question.label}</p>
      {question.type === "multi_select" && <span className="shrink-0 text-[13px] text-muted-foreground">Select all that apply</span>}
      {!question.required && question.type !== "multi_select" && (
        <span className="shrink-0 text-[13px] text-muted-foreground">Optional</span>
      )}
    </div>
  );

  switch (question.type) {
    case "multi_select": {
      const selected = (value as string[] | undefined) ?? [];
      return (
        <div role="group" aria-label={question.label}>
          {label}
          <div className="overflow-hidden rounded-xl bg-card">
            {question.options!.map((o) => (
              <Choice
                key={o.value}
                selected={selected.includes(o.value)}
                onClick={() =>
                  onChange(selected.includes(o.value) ? selected.filter((v) => v !== o.value) : [...selected, o.value])
                }
              >
                {o.label}
              </Choice>
            ))}
          </div>
        </div>
      );
    }
    case "single_select":
      return (
        <div role="group" aria-label={question.label}>
          {label}
          <div className="overflow-hidden rounded-xl bg-card">
            {question.options!.map((o) => (
              <Choice key={o.value} selected={value === o.value} onClick={() => onChange(o.value)}>
                {o.label}
              </Choice>
            ))}
          </div>
        </div>
      );
    case "boolean":
      return (
        <div>
          {label}
          <SegmentedControl
            label={question.label}
            options={[
              { value: true, label: "Yes" },
              { value: false, label: "No" },
            ]}
            value={value as boolean | undefined}
            onChange={onChange}
            className="sm:max-w-xs [&_button]:py-2 [&_button]:text-[15px]"
          />
        </div>
      );
    case "number":
      return (
        <div>
          <label htmlFor={question.id} className="block">
            {label}
          </label>
          <Input
            id={question.id}
            type="number"
            inputMode="decimal"
            min={question.min ?? 0}
            step="any"
            value={value === undefined || value === null ? "" : String(value)}
            onChange={(e) => onChange(e.target.value === "" ? undefined : Number(e.target.value))}
            className="bg-card sm:max-w-xs"
          />
        </div>
      );
  }
}
