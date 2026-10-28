"use client";

import Link from "next/link";
import { useState } from "react";
import { FileText } from "lucide-react";

import { PageHeader } from "@/components/app-shell";
import { Select } from "@/components/controls";
import { EmptyState, IconTile, Loading, Section } from "@/components/list";
import { DocumentActions } from "@/components/requirement-card";
import { UploadZone } from "@/components/upload-zone";
import { formatBytes, formatDate } from "@/lib/format";
import type { DocumentInfo, RegulationSummary } from "@/lib/types";
import { useApi } from "@/lib/use-api";

export default function DocumentsPage() {
  const [regulation, setRegulation] = useState("");
  const { data: regs } = useApi<RegulationSummary[]>("/company/regulations");
  const { data: docs, reload } = useApi<DocumentInfo[]>(`/documents${regulation ? `?regulation=${regulation}` : ""}`);

  return (
    <>
      <PageHeader
        title="Documents"
        description="All the evidence you have uploaded. To link a document to a requirement, add it on the regulation's page."
        action={
          <Select
            label="Filter by regulation"
            value={regulation}
            onChange={setRegulation}
            options={[{ value: "", label: "All Regulations" }, ...(regs ?? []).map((r) => ({ value: r.code, label: r.short_name }))]}
          />
        }
      />

      {!regulation && (
        <div className="mb-8">
          <UploadZone onUploaded={reload} />
        </div>
      )}

      {!docs ? (
        <Loading />
      ) : docs.length === 0 ? (
        <EmptyState>No documents yet.</EmptyState>
      ) : (
        <Section footer={`${docs.length} ${docs.length === 1 ? "document" : "documents"}. Text from readable files is searchable by the assistant.`}>
          {docs.map((d) => (
            <div
              key={d.id}
              className="relative flex items-center gap-3 py-2.5 pr-2 pl-4 not-first:before:absolute not-first:before:top-0 not-first:before:right-0 not-first:before:left-15 not-first:before:h-px not-first:before:bg-border"
            >
              <IconTile icon={FileText} className="bg-[#8e8e93]" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[15px]">{d.filename}</p>
                <p className="truncate text-[13px] text-muted-foreground">
                  {formatBytes(d.size_bytes)} · {formatDate(d.uploaded_at)}
                  {d.regulation_code ? (
                    <>
                      {" · "}
                      <Link href={`/regulations/${d.regulation_code}#req-${d.requirement_id}`} className="text-primary hover:opacity-70">
                        {d.regulation_short_name}: {d.requirement_title}
                      </Link>
                    </>
                  ) : (
                    " · Not linked to a requirement"
                  )}
                </p>
              </div>
              <DocumentActions doc={d} onDeleted={reload} />
            </div>
          ))}
        </Section>
      )}
    </>
  );
}
