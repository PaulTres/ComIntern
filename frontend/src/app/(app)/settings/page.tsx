"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, json } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { isVisible } from "@/lib/format";
import type { QuestionnaireStep } from "@/lib/types";
import { useApi } from "@/lib/use-api";

function display(value: unknown, options?: { value: string; label: string }[]) {
  const label = (v: unknown) => options?.find((o) => o.value === v)?.label ?? String(v);
  if (Array.isArray(value)) return value.map(label).join(", ");
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return label(value);
}

export default function SettingsPage() {
  const { user, refresh } = useAuth();
  const { data: q } = useApi<{ steps: QuestionnaireStep[] }>("/questionnaire");
  const [name, setName] = useState(user?.company.name ?? "");
  const [saving, setSaving] = useState(false);
  const profile = user?.company.profile ?? {};

  async function saveName(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api("/company", { method: "PUT", body: json({ name }) });
      await refresh();
      toast.success("Company name saved");
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageHeader title="Company profile" description="Your answers determine which regulations apply." />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <SectionCard title="Company">
          <form onSubmit={saveName} className="flex flex-col gap-3">
            <Label htmlFor="name">Company name</Label>
            <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            <Button type="submit" disabled={saving || name === user?.company.name} className="self-start">
              {saving && <Loader2 className="animate-spin" />} Save
            </Button>
          </form>
        </SectionCard>

        <SectionCard title="Assessment answers" className="lg:col-span-2">
          <dl className="flex flex-col divide-y">
            {q?.steps.flatMap((s) =>
              s.questions
                .filter((question) => isVisible(question.show_if, profile) && profile[question.id] !== undefined)
                .map((question) => (
                  <div key={question.id} className="grid gap-1 py-3 sm:grid-cols-2 sm:gap-4">
                    <dt className="text-sm text-muted-foreground">{question.label}</dt>
                    <dd className="text-sm font-medium">{display(profile[question.id], question.options)}</dd>
                  </div>
                )),
            )}
          </dl>
          <Link href="/onboarding" className={`${buttonVariants()} mt-4`}>
            Update answers <ArrowRight />
          </Link>
          <p className="mt-2 text-xs text-muted-foreground">
            Updating your answers re-runs the assessment. Your requirement statuses and documents are kept.
          </p>
        </SectionCard>
      </div>
    </>
  );
}
