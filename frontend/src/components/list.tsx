import Link from "next/link";
import { ChevronRight, Loader2, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

/** An inset grouped section, as in iOS Settings: a bold title, a rounded card, an optional footnote. */
export function Section({
  title,
  action,
  footer,
  className,
  children,
}: {
  title?: string;
  action?: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section className={className}>
      {(title || action) && (
        <div className="mb-2 flex min-h-7 items-end justify-between gap-4 px-1">
          {title && <h2 className="text-[20px] leading-tight font-semibold tracking-tight">{title}</h2>}
          {action}
        </div>
      )}
      <div className="overflow-hidden rounded-xl bg-card">{children}</div>
      {footer && <div className="mt-2 px-4 text-[13px] leading-snug text-muted-foreground">{footer}</div>}
    </section>
  );
}

export function SeeAll({ href, label = "See All" }: { href: string; label?: string }) {
  return (
    <Link href={href} className="text-[15px] text-primary hover:opacity-70">
      {label}
    </Link>
  );
}

const ROW =
  "relative flex min-h-11 w-full items-center gap-3 px-4 py-2.5 text-left not-first:before:absolute not-first:before:top-0 not-first:before:right-0 not-first:before:h-px not-first:before:bg-border";
const INTERACTIVE = "transition-colors outline-none hover:bg-foreground/[0.03] focus-visible:bg-foreground/[0.05] active:bg-foreground/[0.08]";

/** One row of a Section. Separators are inset to the text, past the icon when there is one. */
export function Row({
  href,
  onClick,
  icon,
  chevron = Boolean(href),
  className,
  children,
}: {
  href?: string;
  onClick?: () => void;
  icon?: React.ReactNode;
  chevron?: boolean;
  className?: string;
  children: React.ReactNode;
}) {
  const classes = cn(ROW, icon ? "not-first:before:left-15" : "not-first:before:left-4", (href || onClick) && INTERACTIVE, className);
  const content = (
    <>
      {icon}
      <div className="flex min-w-0 flex-1 items-center gap-3">{children}</div>
      {chevron && <ChevronRight className="size-4 shrink-0 text-tertiary-foreground" />}
    </>
  );
  if (href)
    return (
      <Link href={href} className={classes}>
        {content}
      </Link>
    );
  if (onClick)
    return (
      <button type="button" onClick={onClick} className={classes}>
        {content}
      </button>
    );
  return <div className={classes}>{content}</div>;
}

export function RowText({ title, subtitle, className }: { title: React.ReactNode; subtitle?: React.ReactNode; className?: string }) {
  return (
    <div className={cn("min-w-0 flex-1", className)}>
      <div className="truncate text-[15px] leading-snug">{title}</div>
      {subtitle && <div className="truncate text-[13px] leading-snug text-muted-foreground">{subtitle}</div>}
    </div>
  );
}

/** A white symbol on a colored rounded square, like the icons in iOS Settings. */
export function IconTile({ icon: Icon, className }: { icon: LucideIcon; className?: string }) {
  return (
    <span className={cn("flex size-8 shrink-0 items-center justify-center rounded-[8px] bg-blue text-white", className)}>
      <Icon className="size-[18px]" strokeWidth={2.2} />
    </span>
  );
}

export function EmptyState({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-xl bg-card px-6 py-10 text-center text-[15px] text-muted-foreground", className)}>
      {children}
    </div>
  );
}

export function Loading() {
  return (
    <div className="flex justify-center py-24" role="status" aria-label="Loading">
      <Loader2 className="size-6 animate-spin text-muted-foreground" />
    </div>
  );
}
