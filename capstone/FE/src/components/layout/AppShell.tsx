"use client"

import { cn } from "@/lib/utils"

interface AppShellProps {
  sidebar?: React.ReactNode
  panel?: React.ReactNode
  children: React.ReactNode
  className?: string
}

export function AppShell({ sidebar, panel, children, className }: AppShellProps) {
  return (
    <div className={cn("flex h-screen overflow-hidden", className)}>
      {sidebar && (
        <aside
          className="flex w-60 shrink-0 flex-col border-r"
          style={{
            backgroundColor: "var(--surface-2)",
            borderColor: "var(--se-border)",
          }}
        >
          {sidebar}
        </aside>
      )}

      <main className="flex flex-1 flex-col overflow-hidden" style={{ backgroundColor: "var(--bg)" }}>
        {children}
      </main>

      {panel && (
        <div
          className="hidden w-[420px] shrink-0 flex-col border-l lg:flex"
          style={{
            backgroundColor: "var(--surface)",
            borderColor: "var(--se-border)",
          }}
        >
          {panel}
        </div>
      )}
    </div>
  )
}
