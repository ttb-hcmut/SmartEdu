import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center gap-1.5 border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap transition-[background-color,color,opacity,transform] duration-150 outline-none select-none focus-visible:ring-2 focus-visible:ring-[--ring] focus-visible:ring-offset-1 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        // Amber primary CTA — pill radius (form submits, destructive confirms)
        default:
          "rounded-pill bg-[var(--se-primary)] text-white hover:bg-[var(--se-primary-hover)]",
        // Electric-blue CTA — pill radius (navigation, confirm, send)
        accent:
          "rounded-pill bg-[var(--se-accent-btn)] text-white hover:brightness-110",
        // Low-emphasis — subtle blue hover fill
        ghost:
          "rounded-sm hover:bg-[var(--se-accent-subtle)] hover:text-foreground",
        // Toggle / secondary — bordered, subtle hover
        outline:
          "rounded-xs border border-[var(--se-border)] bg-transparent hover:bg-[var(--se-accent-subtle)] hover:text-foreground",
        // Destructive
        destructive:
          "rounded-sm bg-[color-mix(in_oklch,var(--destructive),transparent_90%)] text-destructive hover:bg-[color-mix(in_oklch,var(--destructive),transparent_80%)]",
        // Plain link
        link: "text-[var(--se-accent)] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4",
        sm: "h-7 px-3 text-[0.8rem]",
        lg: "h-11 px-6 text-base",
        icon: "size-9 rounded-sm",
        "icon-sm": "size-7 rounded-xs",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
