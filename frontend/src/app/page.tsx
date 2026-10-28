import Link from "next/link";
import { Bell, ChevronRight, ClipboardList, FolderCheck, MessageCircle, ScrollText } from "lucide-react";

import { IconTile } from "@/components/list";
import { Logo } from "@/components/logo";
import { buttonVariants } from "@/components/ui/button";

const FEATURES = [
  { icon: ClipboardList, color: "bg-blue", title: "Answer a few questions", text: "Size, sector, countries, data and AI use. It takes about five minutes." },
  { icon: ScrollText, color: "bg-indigo", title: "See what applies, and why", text: "Each regulation comes with the reason it applies to you and a weighted checklist." },
  { icon: FolderCheck, color: "bg-green", title: "Collect the evidence", text: "Attach documents to each requirement and watch your readiness score grow." },
  { icon: MessageCircle, color: "bg-teal", title: "Ask the assistant", text: "A local model answers from the official texts and your own evidence, with sources." },
  { icon: Bell, color: "bg-orange", title: "Stay up to date", text: "New deadlines and amendments for the regulations that affect you." },
];

// The catalog in src/comintern/catalog/regulations/*.yaml.
const CATALOG = [
  { title: "European Union", items: ["GDPR", "NIS2", "AI Act", "DORA", "CSRD", "CSDDD", "Whistleblowing (EU)", "AML (EU)"] },
  { title: "Germany", items: ["BDSG", "NIS2 (DE)", "LkSG", "HinSchG", "GwG"] },
  { title: "Romania", items: ["Law 190/2018", "NIS2 (RO)", "Law 361/2022", "Law 129/2019", "RO e-Factura"] },
];

export default function Landing() {
  return (
    <div className="flex flex-1 flex-col">
      <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-13 w-full max-w-5xl items-center justify-between px-4 sm:px-6">
          <Logo />
          <div className="flex items-center gap-1">
            <Link href="/login" className={buttonVariants({ variant: "plain", size: "sm" })}>
              Sign In
            </Link>
            <Link href="/register" className={buttonVariants({ size: "sm" })}>
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="mx-auto max-w-4xl px-4 pt-20 pb-16 text-center sm:px-6 sm:pt-28 sm:pb-24">
          <p className="text-[17px] font-semibold text-primary">For companies in the EU, Germany and Romania</p>
          <h1 className="mx-auto mt-3 text-[40px] leading-[1.05] font-bold tracking-tight text-balance sm:text-[64px]">
            Know which rules apply. Be ready for the audit.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-[19px] leading-relaxed text-muted-foreground text-balance sm:text-[21px]">
            ComIntern finds the regulations your company must follow, turns each one into a checklist and shows you
            where you stand, before an auditor does.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row sm:gap-6">
            <Link href="/register" className={buttonVariants({ size: "lg" })}>
              Start the free assessment
            </Link>
            <Link href="/login" className="inline-flex items-center text-[17px] text-primary hover:opacity-70">
              I have an account <ChevronRight className="size-4" />
            </Link>
          </div>
        </section>

        <section className="bg-card py-16 sm:py-24">
          <div className="mx-auto max-w-5xl px-4 sm:px-6">
            <h2 className="text-[28px] leading-tight font-bold tracking-tight sm:text-[40px]">How it works</h2>
            <div className="mt-10 grid grid-cols-1 gap-x-10 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map(({ icon, color, title, text }) => (
                <div key={title}>
                  <IconTile icon={icon} className={`size-10 rounded-[10px] ${color}`} />
                  <h3 className="mt-4 text-[19px] font-semibold tracking-tight">{title}</h3>
                  <p className="mt-1.5 text-[17px] leading-relaxed text-muted-foreground">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-24">
          <h2 className="text-[28px] leading-tight font-bold tracking-tight sm:text-[40px]">18 regulations, three jurisdictions</h2>
          <div className="mt-10 grid grid-cols-1 gap-8 sm:grid-cols-3">
            {CATALOG.map((group) => (
              <div key={group.title}>
                <h3 className="px-1 text-[13px] font-semibold text-muted-foreground uppercase">{group.title}</h3>
                <ul className="mt-2 overflow-hidden rounded-xl bg-card">
                  {group.items.map((item) => (
                    <li
                      key={item}
                      className="relative flex min-h-11 items-center px-4 text-[15px] not-first:before:absolute not-first:before:top-0 not-first:before:right-0 not-first:before:left-4 not-first:before:h-px not-first:before:bg-border"
                    >
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t">
        <p className="mx-auto max-w-5xl px-4 py-6 text-[12px] text-muted-foreground sm:px-6">
          ComIntern gives guidance, not legal advice. Always confirm your obligations with qualified counsel.
        </p>
      </footer>
    </div>
  );
}
