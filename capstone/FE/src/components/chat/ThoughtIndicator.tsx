"use client"

import { Skeleton } from "@/components/ui/skeleton"
import { type AgentThought } from "@/hooks/useChatPoll"

interface ThoughtIndicatorProps {
  thought: AgentThought | null
}

export function ThoughtIndicator({ thought }: ThoughtIndicatorProps) {
  return (
    <div className="flex items-start gap-2.5 py-2">
      {/* Pulsing amber dot */}
      <span
        className="mt-1 size-2 shrink-0 rounded-full thought-pulse"
        style={{ backgroundColor: "var(--se-primary)" }}
        aria-hidden="true"
      />

      <div className="min-w-0 space-y-1">
        {/* Agent name */}
        <p
          className="font-mono text-[11px] uppercase tracking-wider"
          style={{ color: "var(--ink-muted)" }}
        >
          {thought?.agentName ?? "TA Agent"}
          {thought?.intent ? ` · ${thought.intent}` : ""}
        </p>

        {/* Thought text or skeleton lines */}
        {thought?.thought ? (
          <p
            className="text-xs leading-relaxed"
            style={{ color: "var(--ink-muted)" }}
          >
            {thought.thought}
          </p>
        ) : (
          <div className="space-y-1.5">
            <Skeleton className="h-2.5 w-48" />
            <Skeleton className="h-2.5 w-32" />
          </div>
        )}
      </div>
    </div>
  )
}
