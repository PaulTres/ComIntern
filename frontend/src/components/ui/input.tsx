import * as React from "react"
import { Input as InputPrimitive } from "@base-ui/react/input"
import { cn } from "cn"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        "h-11 w-full min-w-0 rounded-[10px] bg-muted px-3 text-[17px] transition-shadow outline-none placeholder:text-tertiary-foreground focus-visible:ring-3 focus-visible:ring-ring/40 disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:ring-3 aria-invalid:ring-destructive/30 sm:h-10 sm:text-[15px]",
        className
      )}
      {...props}
    />
  )
}

export { Input }
