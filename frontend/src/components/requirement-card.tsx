"use client";

import { useState } from "react";
import { ChevronDown, Download, FileText, Lightbulb, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { StatusBadge } from "@/components/badges";
import { Textarea } from "@/components/ui/textarea";
import { UploadZone } from "@/components/upload-zone";
import { api, downloadDocument, json } from "@/lib/api";
import { STATUS_LABEL, formatBytes, formatDate } from "@/lib/format";
import type { Requirement, Status } from "@/lib/types";
import { cn } from "@/lib/utils";

const STATUSES: Status[] = ["not_started", "in_progress", "compliant", "not_applicable"];

const STATUS_ACTIVE: Record<Status, string> = {
  not_started: "bg-background text-foreground shadow-sm",
  in_progress: "bg-amber-100 text-amber-900 shadow-sm",
  compliant: "bg-emerald-100 text-emerald-900 shadow-sm",
  not_applicable: "bg-slate-200 text-slate-700 shadow-sm",
};

export function RequirementCard({
  requirement: req,
  onChanged,
  defaultOpen = false,
}: {
  requirement: Requirement;
  onChanged: () => void;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [note, setNote] = useState(req.note ?? "");

  async function save(status: Status, newNote = note) {
    try {
      await api(`/requirements/${req.id}/status`, {
        method: "PUT",
        body: json({ status, note: newNote || null }),
      });
      onChanged();
    } catch (e) {
      toast.error((e as Error).message);
    }
  }

  async function remove(id: number) {
    try {
      await api(`/documents/${id}`, { method: "DELETE" });
      onChanged();
      toast.success("Document deleted");
    } catch (e) {
      toast.error((e as Error).message);
    }
  }

  return (
    <div id={`req-${req.id}`} className="scroll-mt-24 rounded-xl border bg-card">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-4 px-5 py-4 text-left"
        aria-expanded={open}
      >
        <div className="min-w-0 flex-1">
          <p className={cn("font-medium", req.status === "not_applicable" && "text-muted-foreground")}>{req.title}</p>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            {req.reference && <span>{req.reference}</span>}
            <span className="inline-flex items-center gap-1" title={`Weight ${req.weight} of 3`}>
              Priority
              {[1, 2, 3].map((i) => (
                <span key={i} className={cn("size-1.5 rounded-full", i <= req.weight ? "bg-primary" : "bg-muted")} />
              ))}
            </span>
            {req.documents.length > 0 && (
              <span className="inline-flex items-center gap-1">
                <FileText className="size-3" /> {req.documents.length}
              </span>
            )}
          </div>
        </div>
        <StatusBadge status={req.status} />
        <ChevronDown className={cn("size-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="flex flex-col gap-5 border-t px-5 py-5">
          <p className="text-sm leading-relaxed">{req.description}</p>
          {req.evidence_hint && (
            <p className="flex gap-2 rounded-lg bg-primary/5 px-3 py-2.5 text-sm">
              <Lightbulb className="mt-0.5 size-4 shrink-0 text-primary" />
              <span>
                <span className="font-medium">Typical evidence: </span>
                <span className="text-muted-foreground">{req.evidence_hint}</span>
              </span>
            </p>
          )}

          <div>
            <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">Status</p>
            <div className="grid grid-cols-2 gap-1 rounded-lg bg-muted p-1 sm:grid-cols-4">
              {STATUSES.map((s) => (
                <button
                  key={s}
                  onClick={() => save(s)}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-sm transition-colors",
                    req.status === s ? STATUS_ACTIVE[s] : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {STATUS_LABEL[s]}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">Evidence</p>
            {req.documents.length > 0 && (
              <ul className="mb-3 flex flex-col divide-y rounded-lg border">
                {req.documents.map((d) => (
                  <li key={d.id} className="flex items-center gap-3 px-3 py-2.5">
                    <FileText className="size-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm">{d.filename}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatBytes(d.size_bytes)} · {formatDate(d.uploaded_at)}
                        {d.has_text && " · indexed for assistant"}
                      </p>
                    </div>
                    <button
                      onClick={() => downloadDocument(d.id, d.filename).catch((e) => toast.error(e.message))}
                      className="text-muted-foreground hover:text-foreground"
                      aria-label="Download"
                    >
                      <Download className="size-4" />
                    </button>
                    <button onClick={() => remove(d.id)} className="text-muted-foreground hover:text-destructive" aria-label="Delete">
                      <Trash2 className="size-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <UploadZone requirementId={req.id} onUploaded={onChanged} compact />
          </div>

          <div>
            <label htmlFor={`note-${req.id}`} className="mb-2 block text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Notes
            </label>
            <Textarea
              id={`note-${req.id}`}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              onBlur={() => note !== (req.note ?? "") && save(req.status, note)}
              placeholder="Who is responsible, what is missing, next audit date…"
              className="min-h-20"
            />
          </div>
        </div>
      )}
    </div>
  );
}
