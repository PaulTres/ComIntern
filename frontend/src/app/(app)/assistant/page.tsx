"use client";

import { useEffect, useState } from "react";
import { Bot, FileText, Loader2, Plus, Send, Sparkles } from "lucide-react";

import { PageHeader } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { type ChatSource, streamChat } from "@/lib/api";
import type { RegulationSummary } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  text: string;
  progress?: string;
  sources?: ChatSource[];
}

const AUDIENCES = [
  { value: "", label: "Plain language" },
  { value: "management", label: "For management" },
  { value: "it", label: "For IT" },
  { value: "legal", label: "For legal" },
];

const EXAMPLES = [
  "What does GDPR Article 30 require us to document?",
  "What should we do next, and which evidence proves it?",
  "How do NIS2 and GDPR overlap on incident reporting?",
];

const SELECT_CLASS =
  "h-9 rounded-lg border bg-card px-3 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/50";

export default function AssistantPage() {
  const { data: regulations } = useApi<RegulationSummary[]>("/company/regulations");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [regulation, setRegulation] = useState("");
  const [audience, setAudience] = useState("");

  // The regulation pages link here with ?regulation=CODE to talk to that regulation's agent.
  useEffect(() => {
    setRegulation(new URLSearchParams(window.location.search).get("regulation") ?? "");
  }, []);

  const updateAnswer = (update: (answer: Message) => Message) =>
    setMessages((current) => [...current.slice(0, -1), update(current[current.length - 1])]);

  async function ask(question: string) {
    if (!question.trim() || busy) return;
    setMessages((current) => [...current, { role: "user", text: question }, { role: "assistant", text: "" }]);
    setInput("");
    setBusy(true);
    try {
      await streamChat(
        {
          content: question,
          conversation_id: conversationId,
          regulation_code: regulation || null,
          audience: audience || null,
        },
        ({ event, data }) => {
          switch (event) {
            case "progress":
              return updateAnswer((answer) => ({ ...answer, progress: data.step }));
            case "delta":
              return updateAnswer((answer) => ({ ...answer, text: answer.text + data.text }));
            case "payload":
              return updateAnswer((answer) => ({ ...answer, sources: data.value }));
            case "final":
              return setConversationId(data.conversation_id);
            case "error":
              return updateAnswer((answer) => ({ ...answer, text: data.detail }));
          }
        },
      );
    } catch (e) {
      updateAnswer((answer) => ({ ...answer, text: (e as Error).message }));
    } finally {
      updateAnswer((answer) => ({ ...answer, progress: undefined }));
      setBusy(false);
    }
  }

  function startNewConversation() {
    setMessages([]);
    setConversationId(null);
  }

  return (
    <>
      <PageHeader
        title="Compliance assistant"
        description="Ask what a regulation says, or what your company should do next. Answers come from the regulation catalog, the official texts and your uploaded evidence."
        action={
          <div className="flex flex-wrap gap-2">
            <select
              value={regulation}
              onChange={(e) => setRegulation(e.target.value)}
              className={SELECT_CLASS}
              aria-label="Regulation agent"
            >
              <option value="">All regulations</option>
              {regulations?.map((r) => (
                <option key={r.code} value={r.code}>
                  {r.short_name} agent
                </option>
              ))}
            </select>
            <select
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              className={SELECT_CLASS}
              aria-label="Write the answer for"
            >
              {AUDIENCES.map((a) => (
                <option key={a.value} value={a.value}>
                  {a.label}
                </option>
              ))}
            </select>
            <Button variant="outline" onClick={startNewConversation} disabled={busy || messages.length === 0}>
              <Plus /> New conversation
            </Button>
          </div>
        }
      />
      <div className="flex min-h-[28rem] flex-col rounded-xl border bg-card">
        <div className="flex flex-1 flex-col gap-4 p-5">
          {messages.length === 0 ? (
            <div className="m-auto max-w-md text-center">
              <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Sparkles className="size-5" />
              </span>
              <p className="mt-4 text-sm text-muted-foreground">
                Pick a regulation above to talk to its agent, which knows your checklist and evidence. The answers
                are guidance from a local model, not legal advice.
              </p>
              <div className="mt-5 flex flex-col gap-2">
                {EXAMPLES.map((example) => (
                  <button
                    key={example}
                    onClick={() => ask(example)}
                    className="rounded-lg border px-3 py-2 text-left text-sm hover:border-primary/40 hover:bg-primary/5"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message, i) => (
              <div key={i} className={cn("flex gap-3", message.role === "user" && "flex-row-reverse")}>
                {message.role === "assistant" && (
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Bot className="size-4" />
                  </span>
                )}
                <div className="flex max-w-[80%] flex-col gap-2">
                  {message.role === "assistant" && !message.text && message.progress && (
                    <p className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="size-4 animate-spin" /> {message.progress}
                    </p>
                  )}
                  {message.text && (
                    <p
                      className={cn(
                        "whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm",
                        message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted",
                      )}
                    >
                      {message.text}
                    </p>
                  )}
                  {message.sources && message.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {message.sources.map((source) => (
                        <span
                          key={source.title}
                          className="inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs text-muted-foreground"
                        >
                          <FileText className="size-3" /> {source.title}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(input);
          }}
          className="flex gap-2 border-t p-3"
        >
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                ask(input);
              }
            }}
            placeholder="Ask about your compliance…"
            className="min-h-10 resize-none"
            rows={1}
          />
          <Button type="submit" size="icon-lg" disabled={busy || !input.trim()} aria-label="Send">
            <Send />
          </Button>
        </form>
      </div>
    </>
  );
}
