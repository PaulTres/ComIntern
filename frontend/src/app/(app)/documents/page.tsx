"use client";

import Link from "next/link";
import { useState } from "react";
import { Download, FileText, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/app-shell";
import { EmptyState } from "@/components/section-card";
import { UploadZone } from "@/components/upload-zone";
import { api, downloadDocument } from "@/lib/api";
import { formatBytes, formatDate } from "@/lib/format";
import type { DocumentInfo, RegulationSummary } from "@/lib/types";
import { useApi } from "@/lib/use-api";

export default function DocumentsPage() {
  const [regulation, setRegulation] = useState("");
  const { data: regs } = useApi<RegulationSummary[]>("/company/regulations");
  const { data: docs, reload } = useApi<DocumentInfo[]>(`/documents${regulation ? `?regulation=${regulation}` : ""}`);

  async function remove(id: number) {
    try {
      await api(`/documents/${id}`, { method: "DELETE" });
      reload();
      toast.success("Document deleted");
    } catch (e) {
      toast.error((e as Error).message);
    }
  }

  return (
    <>
      <PageHeader
        title="Documents"
        description="All evidence you have uploaded. To link a document to a requirement, upload it from the regulation page."
        action={
          <select
            value={regulation}
            onChange={(e) => setRegulation(e.target.value)}
            className="h-9 rounded-lg border bg-card px-3 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            aria-label="Filter by regulation"
          >
            <option value="">All regulations</option>
            {regs?.map((r) => (
              <option key={r.code} value={r.code}>
                {r.short_name}
              </option>
            ))}
          </select>
        }
      />

      {!regulation && (
        <div className="mb-6">
          <UploadZone onUploaded={reload} />
        </div>
      )}

      {!docs ? (
        <div className="flex justify-center py-20">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : docs.length === 0 ? (
        <EmptyState>No documents yet.</EmptyState>
      ) : (
        <div className="overflow-hidden rounded-xl border bg-card">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/40 text-left text-xs text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Document</th>
                <th className="hidden px-4 py-3 font-medium md:table-cell">Linked requirement</th>
                <th className="hidden px-4 py-3 font-medium sm:table-cell">Uploaded</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {docs.map((d) => (
                <tr key={d.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <FileText className="size-4 shrink-0 text-muted-foreground" />
                      <div className="min-w-0">
                        <p className="max-w-[16rem] truncate font-medium">{d.filename}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatBytes(d.size_bytes)}
                          {d.has_text && " · indexed"}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="hidden px-4 py-3 md:table-cell">
                    {d.regulation_code ? (
                      <Link href={`/regulations/${d.regulation_code}#req-${d.requirement_id}`} className="hover:underline">
                        <span className="font-medium">{d.regulation_short_name}</span>
                        <span className="text-muted-foreground"> · {d.requirement_title}</span>
                      </Link>
                    ) : (
                      <span className="text-muted-foreground">Unassigned</span>
                    )}
                  </td>
                  <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">{formatDate(d.uploaded_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-3">
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
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
