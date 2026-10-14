"use client";

import { Check } from "lucide-react";

import { Input } from "@/components/ui/input";
import type { Question } from "@/lib/types";
import { cn } from "@/lib/utils";

function OptionCard({
  selected,
  onClick,
  children,
  indicator = "check",
}: {
  selected: boolean;
  onClick: () => void;
  children: React.ReactNode;
  indicator?: "check" | "radio";
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "flex w-full items-center gap-3 rounded-xl border bg-card px-4 py-3 text-left text-sm transition-all outline-none hover:border-primary/40 focus-visible:ring-3 focus-visible:ring-ring/50",
        selected && "border-primary bg-primary/5 ring-1 ring-primary",
      )}
    >
      <span
        className={cn(
          "flex size-5 shrink-0 items-center justify-center border transition-colors",
          indicator === "radio" ? "rounded-full" : "rounded-md",
          selected ? "border-primary bg-primary text-primary-foreground" : "border-input bg-background",
        )}
      >
        {selected &&
          (indicator === "radio" ? <span className="size-2 rounded-full bg-primary-foreground" /> : <Check className="size-3.5" />)}
      </span>
      <span className="flex-1">{children}</span>
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
    <p className="mb-3 text-sm font-medium">
      {question.label}
      {question.required && <span className="ml-0.5 text-primary">*</span>}
    </p>
  );

  switch (question.type) {
    case "multi_select": {
      const selected = (value as string[] | undefined) ?? [];
      return (
        <div>
          {label}
          <div className="grid gap-2 sm:grid-cols-2">
            {question.options!.map((o) => (
              <OptionCard
                key={o.value}
                selected={selected.includes(o.value)}
                onClick={() =>
                  onChange(selected.includes(o.value) ? selected.filter((v) => v !== o.value) : [...selected, o.value])
                }
              >
                {o.label}
              </OptionCard>
            ))}
          </div>
        </div>
      );
    }
    case "single_select":
      return (
        <div>
          {label}
          <div className={cn("grid gap-2", question.options!.length > 6 ? "sm:grid-cols-2" : "")}>
            {question.options!.map((o) => (
              <OptionCard key={o.value} indicator="radio" selected={value === o.value} onClick={() => onChange(o.value)}>
                {o.label}
              </OptionCard>
            ))}
          </div>
        </div>
      );
    case "boolean":
      return (
        <div>
          {label}
          <div className="grid grid-cols-2 gap-2 sm:max-w-xs">
            {[true, false].map((v) => (
              <OptionCard key={String(v)} indicator="radio" selected={value === v} onClick={() => onChange(v)}>
                {v ? "Yes" : "No"}
              </OptionCard>
            ))}
          </div>
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
            className="h-11 max-w-xs text-base"
          />
        </div>
      );
  }
}
