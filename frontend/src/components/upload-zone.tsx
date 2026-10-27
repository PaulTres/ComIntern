"use client";

import { useRef, useState } from "react";
import { Loader2, UploadCloud } from "lucide-react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";
import { cn } from "@/lib/utils";

const ACCEPT = ".pdf,.docx,.doc,.xlsx,.xls,.pptx,.txt,.md,.csv,.png,.jpg,.jpeg";

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
    <div
      role="button"
      tabIndex={0}
      onClick={() => input.current?.click()}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && input.current?.click()}
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
        "flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed text-sm text-muted-foreground transition-colors outline-none hover:border-primary/50 hover:bg-primary/5 focus-visible:ring-3 focus-visible:ring-ring/50",
        compact ? "px-3 py-3" : "flex-col px-6 py-10",
        dragging && "border-primary bg-primary/5",
      )}
    >
      <input ref={input} type="file" multiple accept={ACCEPT} className="hidden" onChange={(e) => upload(e.target.files)} />
      {busy ? <Loader2 className="size-5 animate-spin" /> : <UploadCloud className={compact ? "size-4" : "size-6"} />}
      <span>
        <span className="font-medium text-foreground">Click to upload</span> or drag evidence here
      </span>
      {!compact && <span className="text-xs">PDF, Word, Excel, PowerPoint, images · max 25 MB</span>}
    </div>
  );
}
