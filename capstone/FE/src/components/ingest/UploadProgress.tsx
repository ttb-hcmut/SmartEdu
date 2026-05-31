"use client"

import { cn } from "@/lib/utils"
import { CheckCircle, XCircle, Loader2 } from "lucide-react"

export type FileStatus = "pending" | "uploading" | "done" | "error"

export interface FileProgress {
  name: string
  status: FileStatus
  progress: number  // 0–100
  error?: string
}

interface UploadProgressProps {
  files: FileProgress[]
  className?: string
}

const statusIcon: Record<FileStatus, React.ReactNode> = {
  pending:   <span className="size-3.5 rounded-full" style={{ backgroundColor: "var(--se-border)" }} />,
  uploading: <Loader2 className="size-3.5 animate-spin" style={{ color: "var(--se-accent)" }} />,
  done:      <CheckCircle className="size-3.5" style={{ color: "var(--success)" }} />,
  error:     <XCircle className="size-3.5" style={{ color: "var(--error)" }} />,
}

export function UploadProgress({ files, className }: UploadProgressProps) {
  if (files.length === 0) return null

  return (
    <ul className={cn("space-y-2", className)}>
      {files.map((f) => (
        <li key={f.name} className="space-y-1">
          <div className="flex items-center gap-2 text-sm">
            {statusIcon[f.status]}
            <span className="flex-1 truncate" style={{ color: "var(--ink)" }}>
              {f.name}
            </span>
            <span className="font-mono text-xs" style={{ color: "var(--ink-muted)" }}>
              {f.status === "uploading" ? `${f.progress}%` : f.status === "done" ? "✓" : ""}
            </span>
          </div>

          {f.status === "uploading" && (
            <div
              className="h-0.5 w-full overflow-hidden rounded-full"
              style={{ backgroundColor: "var(--se-border)" }}
            >
              <div
                className="h-full rounded-full"
                style={{
                  width: `${f.progress}%`,
                  backgroundColor: "var(--se-accent)",
                  transition: "width 200ms ease-out",
                }}
              />
            </div>
          )}

          {f.error && (
            <p className="text-xs" style={{ color: "var(--error)" }}>{f.error}</p>
          )}
        </li>
      ))}
    </ul>
  )
}
