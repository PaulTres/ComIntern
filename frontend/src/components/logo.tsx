import Link from "next/link";
import { ShieldCheck } from "lucide-react";

import { cn } from "@/lib/utils";

export function AppIcon({ className }: { className?: string }) {
  return (
    <span className={cn("flex size-7 items-center justify-center rounded-[8px] bg-primary text-white", className)}>
      <ShieldCheck className="size-[62%]" strokeWidth={2.2} />
    </span>
  );
}

export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="flex items-center gap-2 text-[17px] font-semibold tracking-tight">
      <AppIcon />
      ComIntern
    </Link>
  );
}
