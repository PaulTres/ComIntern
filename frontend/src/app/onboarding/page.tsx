"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Logo } from "@/components/logo";
import { QuestionField } from "@/components/question-field";
import { Button } from "@/components/ui/button";
import { ApiError, api, json } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { isVisible } from "@/lib/format";
import type { Question, QuestionnaireStep } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { cn } from "@/lib/utils";

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

  function next() {
    if (isLast) submit();
    else {
      setStepIndex((i) => i + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  return (
    <div className="flex flex-1 flex-col">
      <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4 sm:px-8">
          <Logo href={user?.company.assessed_at ? "/dashboard" : "/"} />
          {steps.length > 0 && (
            <span className="text-sm text-muted-foreground tabular-nums">
              Step {stepIndex + 1} of {steps.length}
            </span>
          )}
        </div>
        <div className="mx-auto flex max-w-3xl gap-1.5 px-4 pb-4 sm:px-8">
          {steps.map((s, i) => (
            <div
              key={s.id}
              className={cn("h-1 flex-1 rounded-full transition-colors duration-500", i <= stepIndex ? "bg-primary" : "bg-muted")}
            />
          ))}
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-8">
        {!step ? (
          <div className="flex justify-center py-20">
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div key={step.id} className="animate-in fade-in slide-in-from-bottom-2 duration-300">
            <h1 className="text-3xl font-semibold tracking-tight">{step.title}</h1>
            <p className="mt-2 text-muted-foreground">{step.description}</p>
            <div className="mt-10 flex flex-col gap-10">
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

      <footer className="sticky bottom-0 border-t bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4 sm:px-8">
          <Button variant="ghost" disabled={stepIndex === 0} onClick={() => setStepIndex((i) => i - 1)} className="h-10">
            <ArrowLeft /> Back
          </Button>
          <Button disabled={!complete || submitting || !step} onClick={next} className="h-10 px-4">
            {submitting && <Loader2 className="animate-spin" />}
            {isLast ? "See my regulations" : "Continue"}
            {!isLast && <ArrowRight />}
          </Button>
        </div>
      </footer>
    </div>
  );
}
