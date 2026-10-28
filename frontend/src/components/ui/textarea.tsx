import * as React from "react"
import { cn } from "cn"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex field-sizing-content min-h-20 w-full rounded-[10px] bg-muted px-3 py-2.5 text-[17px] transition-shadow outline-none placeholder:text-tertiary-foreground focus-visible:ring-3 focus-visible:ring-ring/40 disabled:cursor-not-allowed disabled:opacity-50 sm:text-[15px]",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
