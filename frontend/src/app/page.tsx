import Link from "next/link";
import { ArrowRight, Bell, ClipboardList, FileCheck2, Gauge } from "lucide-react";

import { Logo } from "@/components/logo";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const STEPS = [
  { icon: ClipboardList, title: "Answer a few questions", text: "Size, sector, countries, data and AI usage – takes about five minutes." },
  { icon: FileCheck2, title: "See what applies", text: "GDPR, NIS2, AI Act, DORA, LkSG, HinSchG, Romanian laws and more – each with the reason why." },
  { icon: Gauge, title: "Track your readiness", text: "Work through requirements, upload evidence and watch your compliance score grow." },
  { icon: Bell, title: "Stay up to date", text: "Get notified about new deadlines and amendments for the regulations that affect you." },
];

const REGS = ["GDPR", "NIS2", "AI Act", "DORA", "CSRD", "CSDDD", "BDSG", "LkSG", "HinSchG", "GwG", "Law 190/2018", "Law 361/2022", "RO e-Factura"];

export default function Landing() {
  return (
    <div className="flex flex-1 flex-col">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-5 sm:px-8">
        <Logo />
        <div className="flex items-center gap-2">
          <Link href="/login" className={buttonVariants({ variant: "ghost" })}>
            Sign in
          </Link>
          <Link href="/register" className={buttonVariants()}>
            Get started
          </Link>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 sm:px-8">
        <section className="py-16 text-center sm:py-24">
          <span className="inline-flex items-center rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground">
            EU · Germany · Romania
          </span>
          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-semibold tracking-tight text-balance sm:text-6xl">
            Know your obligations. <span className="text-primary">Be audit-ready.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground text-balance">
            ComIntern maps the regulations that apply to your company, tracks your evidence requirement by
            requirement and shows you exactly where you stand before the auditor does.
          </p>
          <div className="mt-10 flex justify-center gap-3">
            <Link href="/register" className={cn(buttonVariants({ size: "lg" }), "h-11 px-5 text-base")}>
              Start free assessment <ArrowRight />
            </Link>
          </div>
          <div className="mx-auto mt-14 flex max-w-3xl flex-wrap justify-center gap-2">
            {REGS.map((r) => (
              <span key={r} className="rounded-md border bg-card px-2.5 py-1 text-xs text-muted-foreground">
                {r}
              </span>
            ))}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-4 pb-24 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <div key={title} className="rounded-xl border bg-card p-6">
              <div className="flex items-center justify-between">
                <span className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="size-4.5" />
                </span>
                <span className="text-xs text-muted-foreground">0{i + 1}</span>
              </div>
              <h3 className="mt-4 font-medium">{title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{text}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t py-6 text-center text-xs text-muted-foreground">
        ComIntern provides guidance, not legal advice. Always verify obligations with qualified counsel.
      </footer>
    </div>
  );
}
