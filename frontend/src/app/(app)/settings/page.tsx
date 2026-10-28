"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/app-shell";
import { Row, Section } from "@/components/list";
import { Button } from "@/components/ui/button";
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
  const { user, refresh, logout } = useAuth();
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

  const answers = q?.steps.flatMap((s) =>
    s.questions.filter((question) => isVisible(question.show_if, profile) && profile[question.id] !== undefined),
  );

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Company" description="Your answers decide which regulations apply." />

      <div className="flex flex-col gap-8">
        <Section title="Name">
          <form onSubmit={saveName} className="flex min-h-12 items-center gap-3 py-1.5 pr-2 pl-4">
            <label htmlFor="name" className="sr-only">
              Company name
            </label>
            <input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="h-10 min-w-0 flex-1 bg-transparent text-[17px] outline-none sm:text-[15px]"
            />
            <Button type="submit" size="sm" disabled={saving || name === user?.company.name}>
              {saving && <Loader2 className="animate-spin" />} Save
            </Button>
          </form>
        </Section>

        <Section
          title="Assessment"
          footer="Changing your answers runs the assessment again. Your requirement statuses and documents are kept."
        >
          {answers?.map((question) => (
            <Row key={question.id}>
              <div className="flex w-full flex-col gap-0.5 sm:flex-row sm:items-center sm:gap-6">
                <span className="text-[15px] sm:w-1/2">{question.label}</span>
                <span className="text-[15px] text-muted-foreground sm:flex-1 sm:text-right">
                  {display(profile[question.id], question.options)}
                </span>
              </div>
            </Row>
          ))}
          <Row href="/onboarding">
            <span className="text-[15px] text-primary">Change Answers</span>
          </Row>
        </Section>

        <Section title="Account">
          <Row>
            <span className="text-[15px]">Email</span>
            <span className="ml-auto truncate text-[15px] text-muted-foreground">{user?.email}</span>
          </Row>
          <Row onClick={logout} chevron={false}>
            <span className="text-[15px] text-red">Sign Out</span>
          </Row>
        </Section>
      </div>
    </div>
  );
}
