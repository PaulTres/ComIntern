"use client";

import { useState } from "react";
import { Bot, Loader2, Send, Sparkles } from "lucide-react";

import { PageHeader } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api, json } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  text: string;
}

const EXAMPLES = [
  "What is still missing for our NIS2 audit?",
  "Does our privacy policy cover all GDPR Art. 13 items?",
  "Which documents do we need for the HinSchG reporting office?",
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function ask(question: string) {
    if (!question.trim()) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setBusy(true);
    try {
      const res = await api<{ answer: string }>("/assistant/ask", { method: "POST", body: json({ question }) });
      setMessages((m) => [...m, { role: "assistant", text: res.answer }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: (e as Error).message }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Compliance assistant"
        description="Coming soon: ask questions about your obligations and get answers grounded in the regulations and your uploaded evidence."
      />
      <div className="flex min-h-[28rem] flex-col rounded-xl border bg-card">
        <div className="flex flex-1 flex-col gap-4 p-5">
          {messages.length === 0 ? (
            <div className="m-auto max-w-md text-center">
              <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Sparkles className="size-5" />
              </span>
              <p className="mt-4 text-sm text-muted-foreground">
                The assistant will use retrieval over official regulation texts and the documents you upload. Try a
                question to see how it will work.
              </p>
              <div className="mt-5 flex flex-col gap-2">
                {EXAMPLES.map((e) => (
                  <button
                    key={e}
                    onClick={() => ask(e)}
                    className="rounded-lg border px-3 py-2 text-left text-sm hover:border-primary/40 hover:bg-primary/5"
                  >
                    {e}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={cn("flex gap-3", m.role === "user" && "flex-row-reverse")}>
                {m.role === "assistant" && (
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Bot className="size-4" />
                  </span>
                )}
                <p
                  className={cn(
                    "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm",
                    m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted",
                  )}
                >
                  {m.text}
                </p>
              </div>
            ))
          )}
          {busy && <Loader2 className="size-4 animate-spin text-muted-foreground" />}
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
