"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Loading } from "@/components/list";
import { QuestionField } from "@/components/question-field";
import { Button } from "@/components/ui/button";
import { ApiError, api, json } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { isVisible } from "@/lib/format";
import type { Question, QuestionnaireStep } from "@/lib/types";
import { useApi } from "@/lib/use-api";

type Answers = Record<string, unknown>;

function isAnswered(q: Question, v: unknown) {
  if (v === undefined || v === null || v === "") return false;
  if (Array.isArray(v)) return v.length > 0;
  if (q.type === "number") return typeof v === "number" && !Number.isNaN(v) && v >= (q.min ?? 0);
  return true;
}

export default function OnboardingPage() {
  const router = useRouter();
  const { user, refresh } = useAuth();
  const { data } = useApi<{ steps: QuestionnaireStep[] }>("/questionnaire");
  // RequireAuth renders this page only once the user is loaded.
  const [answers, setAnswers] = useState<Answers>(() => user?.company.profile ?? {});
  const [stepIndex, setStepIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  const steps = data?.steps ?? [];
  const step = steps[stepIndex];
  const questions = useMemo(
    () => step?.questions.filter((q) => isVisible(q.show_if, answers)) ?? [],
    [step, answers],
  );
  const complete = questions.every((q) => !q.required || isAnswered(q, answers[q.id]));
  const isLast = stepIndex === steps.length - 1;

  async function submit() {
    setSubmitting(true);
    try {
      await api("/company", { method: "PUT", body: json({ profile: answers }) });
      await refresh();
      router.push("/onboarding/result");
    } catch (e) {
      const errors = e instanceof ApiError ? (e.detail as { errors?: Record<string, string> })?.errors : undefined;
      toast.error(errors ? `Please check: ${Object.keys(errors).join(", ")}` : (e as Error).message);
      setSubmitting(false);
    }
  }

  function go(index: number) {
    setStepIndex(index);
    window.scrollTo({ top: 0 });
  }

  return (
    <div className="flex flex-1 flex-col">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto grid h-13 max-w-2xl grid-cols-[1fr_auto_1fr] items-center px-4 sm:px-6">
          <Link
            href={user?.company.assessed_at ? "/dashboard" : "/"}
            className="justify-self-start text-[17px] text-primary hover:opacity-70"
          >
            Cancel
          </Link>
          {steps.length > 0 && (
            <span className="text-[15px] font-semibold tabular-nums">
              {stepIndex + 1} of {steps.length}
            </span>
          )}
        </div>
        <div className="h-0.5 bg-border">
          <div
            className="h-full bg-primary transition-[width] duration-500 ease-out"
            style={{ width: steps.length ? `${((stepIndex + 1) / steps.length) * 100}%` : 0 }}
          />
        </div>
      </header>

      <main className="mx-auto w-full max-w-2xl flex-1 px-4 pt-8 pb-12 sm:px-6 sm:pt-12">
        {!step ? (
          <Loading />
        ) : (
          <div key={step.id} className="animate-in fade-in slide-in-from-right-4 duration-300">
            <h1 className="text-[28px] leading-tight font-bold tracking-tight sm:text-[34px]">{step.title}</h1>
            <p className="mt-2 text-[17px] text-muted-foreground">{step.description}</p>
            <div className="mt-8 flex flex-col gap-8">
              {questions.map((q) => (
                <QuestionField
                  key={q.id}
                  question={q}
                  value={answers[q.id]}
                  onChange={(v) => setAnswers((a) => ({ ...a, [q.id]: v }))}
                />
              ))}
            </div>
          </div>
        )}
      </main>

      <footer className="sticky bottom-0 border-t bg-background/80 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl">
        <div className="mx-auto flex max-w-2xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Button variant="plain" disabled={stepIndex === 0} onClick={() => go(stepIndex - 1)}>
            Back
          </Button>
          <Button size="lg" disabled={!complete || submitting || !step} onClick={() => (isLast ? submit() : go(stepIndex + 1))}>
            {submitting && <Loader2 className="animate-spin" />}
            {isLast ? "See My Regulations" : "Continue"}
          </Button>
        </div>
      </footer>
    </div>
  );
}
