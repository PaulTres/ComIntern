import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"

// Apple-style capsule buttons: filled for the main action, tinted for secondary ones, plain for text links.
const buttonVariantsRaw = cva(
  "inline-flex shrink-0 items-center justify-center gap-1.5 rounded-full font-medium whitespace-nowrap transition-[opacity,background-color] outline-none select-none focus-visible:ring-3 focus-visible:ring-ring/50 active:opacity-60 disabled:pointer-events-none disabled:opacity-40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        tinted: "bg-primary/12 text-primary hover:bg-primary/18",
        gray: "bg-muted text-foreground hover:bg-foreground/10",
        plain: "text-primary hover:bg-primary/8",
        destructive: "bg-destructive/12 text-destructive hover:bg-destructive/18",
      },
      size: {
        default: "h-9 px-4 text-[15px]",
        sm: "h-8 px-3 text-[13px]",
        lg: "h-12 px-6 text-[17px]",
        icon: "size-9",
        "icon-sm": "size-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

// Resolve conflicting classes when a caller adds its own.
const buttonVariants = (props?: Parameters<typeof buttonVariantsRaw>[0]) => cn(buttonVariantsRaw(props))

function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariantsRaw>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
