export type Status = "not_started" | "in_progress" | "compliant" | "not_applicable";
export type Level = "green" | "amber" | "red" | "none";

export interface Company {
  id: number;
  name: string;
  profile: Record<string, unknown> | null;
  assessed_at: string | null;
}

export interface User {
  id: number;
  email: string;
  company: Company;
}

export interface Score {
  score: number | null;
  level: Level;
  total: number;
  compliant: number;
  in_progress: number;
  not_started: number;
  not_applicable: number;
  evidenced: number;
}

export interface RegulationSummary {
  code: string;
  name: string;
  short_name: string;
  jurisdiction: "EU" | "DE" | "RO";
  category: string;
  summary: string;
  reasons: string[];
  score: Score;
}

export interface DocumentInfo {
  id: number;
  filename: string;
  mime_type: string | null;
  size_bytes: number;
  uploaded_at: string;
  has_text: boolean;
  requirement_id: number | null;
  requirement_title: string | null;
  regulation_code: string | null;
  regulation_short_name: string | null;
}

export interface Requirement {
  id: number;
  key: string;
  title: string;
  description: string;
  reference: string | null;
  weight: number;
  evidence_hint: string | null;
  status: Status;
  note: string | null;
  updated_at: string | null;
  documents: DocumentInfo[];
}

export interface RegulatoryUpdate {
  id: number;
  regulation_code: string;
  title: string;
  summary: string;
  published_on: string;
  effective_on: string | null;
  kind: "deadline" | "amendment" | "guidance";
  severity: "info" | "important" | "critical";
  source_url: string | null;
  relevant: boolean;
}

export interface RegulationDetail extends RegulationSummary {
  authority: string | null;
  source_url: string | null;
  requirements: Requirement[];
  updates: RegulatoryUpdate[];
}

export interface OpenTask {
  requirement_id: number;
  title: string;
  status: Status;
  weight: number;
  regulation_code: string;
  regulation_short_name: string;
}

export interface Dashboard {
  company_name: string;
  assessed: boolean;
  overall_score: number | null;
  level: Level;
  totals: Score;
  regulations: RegulationSummary[];
  open_tasks: OpenTask[];
  recent_documents: DocumentInfo[];
  updates: RegulatoryUpdate[];
}

export interface Condition {
  field?: string;
  op?: string;
  value?: unknown;
}

export interface Question {
  id: string;
  type: "multi_select" | "single_select" | "boolean" | "number";
  label: string;
  required?: boolean;
  min?: number;
  options?: { value: string; label: string }[];
  show_if?: Condition;
}

export interface QuestionnaireStep {
  id: string;
  title: string;
  description: string;
  questions: Question[];
}
