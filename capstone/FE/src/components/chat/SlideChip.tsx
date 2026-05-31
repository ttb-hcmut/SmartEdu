"use client"

import { FileText } from "lucide-react"
import { cn } from "@/lib/utils"

interface SlideChipProps {
  page: number
  visible: boolean
  onClick: () => void
  className?: string
}

export function SlideChip({ page, visible, onClick, className }: SlideChipProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-1.5 rounded-pill px-3 py-1 text-xs font-medium transition-colors",
        "hover:brightness-105 active:scale-95",
        className
      )}
      style={{
        backgroundColor: "var(--se-accent-subtle)",
        color: "var(--se-accent)",
        border: "1px solid",
        borderColor: visible
          ? "color-mix(in oklch, var(--se-accent) 30%, transparent)"
          : "var(--se-border)",
        opacity: visible ? 1 : 0.7,
      }}
      title={visible ? `Tới trang ${page}` : `Mở trang ${page} trong PDF viewer`}
    >
      <FileText className="size-3" aria-hidden="true" />
      {visible ? `Trang ${page}` : `Xem slide ${page}`}
    </button>
  )
}
