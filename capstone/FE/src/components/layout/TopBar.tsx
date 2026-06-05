"use client"

import { useAuth } from "@/contexts/AuthContext"
import { Settings, ArrowLeft } from "lucide-react"
import Link from "next/link"

interface TopBarProps {
  title?: string
  backHref?: string
}

export function TopBar({ title, backHref }: TopBarProps) {
  const { sessionId } = useAuth()

  return (
    <header
      className="flex h-12 shrink-0 items-center gap-3 border-b px-4"
      style={{
        backgroundColor: "var(--bg)",
        borderColor: "var(--se-border)",
      }}
    >
      {backHref && (
        <Link
          href={backHref}
          aria-label="Quay lại"
          className="flex size-7 items-center justify-center rounded-xs transition-colors hover:bg-[var(--se-accent-subtle)]"
          style={{ color: "var(--ink-muted)" }}
        >
          <ArrowLeft className="size-4" />
        </Link>
      )}

      {title && (
        <span
          className="text-sm font-medium"
          style={{ color: "var(--ink)" }}
        >
          {title}
        </span>
      )}

      <div className="ml-auto flex items-center gap-2">
        {sessionId && (
          <span
            className="flex items-center gap-1.5 text-xs"
            style={{ color: "var(--ink-muted)" }}
          >
            <span
              className="size-1.5 rounded-full"
              style={{ backgroundColor: "var(--success)" }}
            />
            Phiên đang hoạt động
          </span>
        )}

        <Link
          href="/settings"
          aria-label="Cài đặt"
          className="flex size-7 items-center justify-center rounded-xs transition-colors hover:bg-[var(--se-accent-subtle)]"
          style={{ color: "var(--ink-muted)" }}
        >
          <Settings className="size-4" />
        </Link>
      </div>
    </header>
  )
}
