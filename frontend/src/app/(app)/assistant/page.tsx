"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, FileText, MessageCircle, SquarePen } from "lucide-react";

import { PageHeader } from "@/components/app-shell";
import { Select } from "@/components/controls";
import { IconTile, Row } from "@/components/list";
import { Button } from "@/components/ui/button";
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
  { value: "", label: "Plain Language" },
  { value: "management", label: "For Management" },
  { value: "it", label: "For IT" },
  { value: "legal", label: "For Legal" },
];

const EXAMPLES = [
  "What does GDPR Article 30 require us to document?",
  "What should we do next, and which evidence proves it?",
  "How do NIS2 and GDPR overlap on incident reporting?",
];

function TypingIndicator() {
  return (
    <span className="flex h-5 items-center gap-1" aria-hidden>
      {[0, 150, 300].map((delay) => (
        <span key={delay} className="size-2 animate-bounce rounded-full bg-muted-foreground/60" style={{ animationDelay: `${delay}ms` }} />
      ))}
    </span>
  );
}

export default function AssistantPage() {
  const { data: regulations } = useApi<RegulationSummary[]>("/company/regulations");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [regulation, setRegulation] = useState("");
  const [audience, setAudience] = useState("");
  const end = useRef<HTMLDivElement>(null);

  // The regulation pages link here with ?regulation=CODE to talk to that regulation's agent.
  useEffect(() => {
    setRegulation(new URLSearchParams(window.location.search).get("regulation") ?? "");
  }, []);

  useEffect(() => {
    end.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages.length]);

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

  const agentName = regulations?.find((r) => r.code === regulation)?.short_name;

  return (
    <>
      <PageHeader
        title="Assistant"
        description="Answers come from the regulation catalog, the official texts and your evidence."
      />

      <div className="mb-3 flex items-start gap-2">
        <div className="flex min-w-0 flex-1 flex-wrap gap-2">
        <Select
          label="Agent"
          value={regulation}
          onChange={setRegulation}
          options={[
            { value: "", label: "All Regulations" },
            ...(regulations ?? []).map((r) => ({ value: r.code, label: `${r.short_name} Agent` })),
          ]}
        />
        <Select label="Write the answer for" value={audience} onChange={setAudience} options={AUDIENCES} />
        </div>
        <Button
          variant="gray"
          size="icon"
          onClick={startNewConversation}
          disabled={busy || messages.length === 0}
          aria-label="New conversation"
          title="New conversation"
        >
          <SquarePen className="size-[18px]" />
        </Button>
      </div>

      <div className="flex min-h-[calc(100dvh-22rem)] flex-col rounded-xl bg-card lg:min-h-[calc(100dvh-20rem)]">
        <div className="flex flex-1 flex-col gap-1.5 p-4" aria-live="polite">
          {messages.length === 0 ? (
            <div className="m-auto flex w-full max-w-md flex-col items-center py-6 text-center">
              <IconTile icon={MessageCircle} className="size-14 rounded-[14px] bg-teal [&_svg]:size-7" />
              <h2 className="mt-4 text-[22px] font-bold tracking-tight">
                {agentName ? `Ask the ${agentName} agent` : "Ask about your compliance"}
              </h2>
              <p className="mt-1.5 text-[15px] text-muted-foreground">
                {agentName
                  ? "It knows this regulation, your checklist and your evidence."
                  : "Choose a regulation's agent above for answers about your own checklist."}
              </p>
              <div className="mt-6 w-full overflow-hidden rounded-xl bg-muted/60 text-left">
                {EXAMPLES.map((example) => (
                  <Row key={example} onClick={() => ask(example)}>
                    <span className="text-[15px] text-primary">{example}</span>
                  </Row>
                ))}
              </div>
              <p className="mt-4 text-[12px] text-tertiary-foreground">
                Answers come from a model running on this computer. They are guidance, not legal advice.
              </p>
            </div>
          ) : (
            messages.map((message, i) => {
              const mine = message.role === "user";
              const previousSameSide = messages[i - 1]?.role === message.role;
              return (
                <div key={i} className={cn("flex max-w-[85%] flex-col gap-1 sm:max-w-[75%]", mine ? "self-end items-end" : "self-start items-start", !previousSameSide && i > 0 && "mt-3")}>
                  <div
                    className={cn(
                      "rounded-[18px] px-3.5 py-2 text-[17px] leading-snug whitespace-pre-wrap sm:text-[15px]",
                      mine ? "bg-primary text-white" : "bg-bubble",
                    )}
                  >
                    {message.text || <TypingIndicator />}
                  </div>
                  {!mine && message.progress && !message.text && (
                    <p className="px-1 text-[12px] text-muted-foreground">{message.progress}</p>
                  )}
                  {message.sources && message.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1 px-1">
                      {message.sources.map((source) => (
                        <span key={source.title} className="inline-flex items-center gap-1 text-[12px] text-muted-foreground">
                          <FileText className="size-3" /> {source.title}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
          <div ref={end} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(input);
          }}
          className="sticky bottom-[calc(env(safe-area-inset-bottom)+51px)] flex items-end gap-2 rounded-b-xl border-t bg-card/90 p-2.5 backdrop-blur-xl lg:bottom-0"
        >
          <label htmlFor="question" className="sr-only">
            Your question
          </label>
          <div className="flex min-w-0 flex-1 items-end rounded-[20px] border border-foreground/15 bg-card pr-1 focus-within:border-primary/60">
            <textarea
              id="question"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  ask(input);
                }
              }}
              placeholder={agentName ? `Message the ${agentName} agent` : "Message"}
              rows={1}
              className="field-sizing-content max-h-40 min-h-9 min-w-0 flex-1 resize-none bg-transparent px-3.5 py-[7px] text-[17px] leading-snug outline-none placeholder:text-tertiary-foreground sm:text-[15px] sm:py-2"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              aria-label="Send"
              className="mb-1 flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-white transition-opacity disabled:opacity-30"
            >
              <ArrowUp className="size-4" strokeWidth={3} />
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
