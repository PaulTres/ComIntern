"use client";

import { useRef, useState } from "react";
import { Loader2, Plus, Upload } from "lucide-react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";
import { cn } from "@/lib/utils";

const ACCEPT = ".pdf,.docx,.doc,.xlsx,.xls,.pptx,.txt,.md,.csv,.png,.jpg,.jpeg";

/** Click or drop files to upload them; with a requirement id they become its evidence. */
export function UploadZone({
  requirementId,
  onUploaded,
  compact = false,
}: {
  requirementId?: number;
  onUploaded: (doc: DocumentInfo) => void;
  compact?: boolean;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);

  async function upload(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    for (const file of Array.from(files)) {
      const form = new FormData();
      form.append("file", file);
      if (requirementId) form.append("requirement_id", String(requirementId));
      try {
        const doc = await api<DocumentInfo>("/documents", { method: "POST", body: form });
        onUploaded(doc);
        toast.success(`Uploaded ${doc.filename}`);
      } catch (e) {
        toast.error(`${file.name}: ${(e as Error).message}`);
      }
    }
    setBusy(false);
    if (input.current) input.current.value = "";
  }

  return (
    <button
      type="button"
      disabled={busy}
      onClick={() => input.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        upload(e.dataTransfer.files);
      }}
      className={cn(
        "flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-foreground/12 text-[15px] text-muted-foreground transition-colors outline-none hover:border-primary/40 hover:bg-primary/[0.03] focus-visible:ring-3 focus-visible:ring-ring/50",
        compact ? "min-h-11 px-4 py-2.5" : "flex-col bg-card px-6 py-10",
        dragging && "border-primary bg-primary/5",
      )}
    >
      <input ref={input} type="file" multiple accept={ACCEPT} className="hidden" onChange={(e) => upload(e.target.files)} />
      {busy ? (
        <Loader2 className="size-5 animate-spin" />
      ) : compact ? (
        <Plus className="size-4 text-primary" />
      ) : (
        <span className="flex size-11 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Upload className="size-5" />
        </span>
      )}
      <span>
        {compact ? (
          <span className="text-primary">Add evidence</span>
        ) : (
          <>
            Drop files here or <span className="text-primary">choose files</span>
          </>
        )}
      </span>
      {!compact && <span className="text-[13px] text-tertiary-foreground">PDF, Word, Excel, PowerPoint, text or images, up to 25 MB</span>}
    </button>
  );
}
