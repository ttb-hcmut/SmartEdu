"use client"

import { cn } from "@/lib/utils"

function AmbientPattern({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={cn("pointer-events-none absolute inset-0 h-full w-full", className)}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <pattern
          id="ambient-dots"
          x="0"
          y="0"
          width="24"
          height="24"
          patternUnits="userSpaceOnUse"
        >
          <circle cx="12" cy="12" r="1.2" fill="currentColor" />
        </pattern>
      </defs>
      <rect
        width="100%"
        height="100%"
        fill="url(#ambient-dots)"
        className="text-[var(--se-border)] opacity-80 dark:text-[var(--se-accent)] dark:opacity-15"
      />
    </svg>
  )
}

interface AuthFrameProps {
  heading: string
  subheading: string
  brandLine?: string
  children: React.ReactNode
  className?: string
}

export function AuthFrame({
  heading,
  subheading,
  brandLine = "SmartEdu",
  children,
  className,
}: AuthFrameProps) {
  return (
    <div className={cn("flex min-h-dvh", className)}>
      {/* ── Left brand panel (md+) ── */}
      <div
        className="relative hidden w-2/5 flex-col justify-between overflow-hidden p-12 md:flex"
        style={{ backgroundColor: "var(--surface-2)" }}
      >
        <AmbientPattern />

        {/* Brand mark */}
        <div className="relative z-10">
          <span
            className="font-mono text-xs uppercase tracking-[0.15em]"
            style={{ color: "var(--se-primary)" }}
          >
            {brandLine}
          </span>
        </div>

        {/* Headline copy */}
        <div className="relative z-10 space-y-3">
          <h1
            className="text-3xl font-semibold leading-tight"
            style={{ color: "var(--ink)" }}
          >
            {heading}
          </h1>
          <p
            className="max-w-xs text-sm leading-relaxed"
            style={{ color: "var(--ink-muted)" }}
          >
            {subheading}
          </p>
        </div>

        {/* Amber accent rule */}
        <div
          className="relative z-10 h-px w-12"
          style={{ backgroundColor: "var(--se-primary)" }}
        />
      </div>

      {/* ── Right form panel ── */}
      <div
        className="flex flex-1 flex-col items-center justify-center px-6 py-12"
        style={{ backgroundColor: "var(--bg)" }}
      >
        {/* Mobile-only brand + heading */}
        <div className="mb-8 text-center md:hidden">
          <span
            className="mb-3 block font-mono text-xs uppercase tracking-[0.15em]"
            style={{ color: "var(--se-primary)" }}
          >
            {brandLine}
          </span>
          <h1
            className="text-2xl font-semibold"
            style={{ color: "var(--ink)" }}
          >
            {heading}
          </h1>
          <p
            className="mt-1 text-sm"
            style={{ color: "var(--ink-muted)" }}
          >
            {subheading}
          </p>
        </div>

        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  )
}
