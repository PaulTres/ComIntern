"use client";

import { useState } from "react";
import { ChevronDown, Download, FileText, Lightbulb, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { StatusBadge } from "@/components/badges";
import { Select } from "@/components/controls";
import { Textarea } from "@/components/ui/textarea";
import { UploadZone } from "@/components/upload-zone";
import { api, downloadDocument, json } from "@/lib/api";
import { STATUS_LABEL, formatBytes, formatDate } from "@/lib/format";
import type { DocumentInfo, Requirement, Status } from "@/lib/types";
import { cn } from "@/lib/utils";

const STATUS_OPTIONS = (Object.keys(STATUS_LABEL) as Status[]).map((s) => ({ value: s, label: STATUS_LABEL[s] }));

/** Asks first, then deletes a document; shared with the documents page. */
export async function deleteDocument(doc: DocumentInfo, onDeleted: () => void) {
  if (!window.confirm(`Delete “${doc.filename}”? This cannot be undone.`)) return;
  try {
    await api(`/documents/${doc.id}`, { method: "DELETE" });
    onDeleted();
    toast.success("Document deleted");
  } catch (e) {
    toast.error((e as Error).message);
  }
}

export function DocumentActions({ doc, onDeleted }: { doc: DocumentInfo; onDeleted: () => void }) {
  return (
    <div className="flex shrink-0 items-center">
      <button
        onClick={() => downloadDocument(doc.id, doc.filename).catch((e) => toast.error(e.message))}
        className="flex size-9 items-center justify-center rounded-full text-primary hover:bg-primary/10"
        aria-label={`Download ${doc.filename}`}
      >
        <Download className="size-[18px]" />
      </button>
      <button
        onClick={() => deleteDocument(doc, onDeleted)}
        className="flex size-9 items-center justify-center rounded-full text-red hover:bg-red/10"
        aria-label={`Delete ${doc.filename}`}
      >
        <Trash2 className="size-[18px]" />
      </button>
    </div>
  );
}

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

  return (
    <div id={`req-${req.id}`} className="scroll-mt-6 overflow-hidden rounded-xl bg-card">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors outline-none hover:bg-foreground/[0.03] focus-visible:bg-foreground/[0.05]"
        aria-expanded={open}
      >
        <div className="min-w-0 flex-1">
          <p className={cn("text-[15px] leading-snug font-semibold", req.status === "not_applicable" && "text-muted-foreground")}>
            {req.title}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[13px] text-muted-foreground">
            {req.reference && <span>{req.reference}</span>}
            <span className="inline-flex items-center gap-1" title={`Priority ${req.weight} of 3`}>
              <span className="sr-only">Priority {req.weight} of 3</span>
              {[1, 2, 3].map((i) => (
                <span key={i} aria-hidden className={cn("h-2.5 w-1 rounded-full", i <= req.weight ? "bg-primary" : "bg-foreground/15")} />
              ))}
            </span>
            {req.documents.length > 0 && (
              <span className="inline-flex items-center gap-1">
                <FileText className="size-3.5" /> {req.documents.length}
              </span>
            )}
          </div>
        </div>
        <StatusBadge status={req.status} />
        <ChevronDown className={cn("size-4 shrink-0 text-tertiary-foreground transition-transform duration-200", open && "rotate-180")} />
      </button>

      {open && (
        <div className="flex flex-col gap-5 border-t px-4 pt-4 pb-5">
          <p className="text-[15px] leading-relaxed">{req.description}</p>
          {req.evidence_hint && (
            <div className="flex gap-2.5 rounded-xl bg-primary/8 px-3.5 py-3 text-[15px] leading-snug">
              <Lightbulb className="mt-0.5 size-4 shrink-0 text-primary" />
              <p>
                <span className="font-semibold">Typical evidence: </span>
                <span className="text-muted-foreground">{req.evidence_hint}</span>
              </p>
            </div>
          )}

          <div className="flex items-center justify-between gap-4">
            <span className="text-[15px] font-semibold">Status</span>
            <Select label="Status" value={req.status} onChange={(s) => save(s as Status)} options={STATUS_OPTIONS} />
          </div>

          <div>
            <p className="mb-2 text-[15px] font-semibold">Evidence</p>
            {req.documents.length > 0 && (
              <ul className="mb-2 overflow-hidden rounded-xl bg-muted/60">
                {req.documents.map((d) => (
                  <li
                    key={d.id}
                    className="relative flex items-center gap-3 py-2 pr-1 pl-3 not-first:before:absolute not-first:before:top-0 not-first:before:right-0 not-first:before:left-10 not-first:before:h-px not-first:before:bg-border"
                  >
                    <FileText className="size-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[15px]">{d.filename}</p>
                      <p className="text-[12px] text-muted-foreground">
                        {formatBytes(d.size_bytes)} · {formatDate(d.uploaded_at)}
                        {d.has_text && " · readable by the assistant"}
                      </p>
                    </div>
                    <DocumentActions doc={d} onDeleted={onChanged} />
                  </li>
                ))}
              </ul>
            )}
            <UploadZone requirementId={req.id} onUploaded={onChanged} compact />
          </div>

          <div>
            <label htmlFor={`note-${req.id}`} className="mb-2 block text-[15px] font-semibold">
              Notes
            </label>
            <Textarea
              id={`note-${req.id}`}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              onBlur={() => note !== (req.note ?? "") && save(req.status, note)}
              placeholder="Who is responsible, what is missing, next audit date…"
            />
            <p className="mt-1.5 px-1 text-[12px] text-muted-foreground">Saved when you leave the field.</p>
          </div>
        </div>
      )}
    </div>
  );
}
