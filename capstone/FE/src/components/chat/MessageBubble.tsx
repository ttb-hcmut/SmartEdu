"use client"

import ReactMarkdown from "react-markdown"
import { type UiAction } from "@/lib/normalise"
import { SlideChip } from "./SlideChip"
import { cn } from "@/lib/utils"

export interface Message {
  id: string
  role: "user" | "ta"
  content: string
  uiAction?: UiAction | null
}

interface MessageBubbleProps {
  message: Message
  pdfOpen: boolean
  onNavigate: (course: string, topic: string, page: number) => void
}

export function MessageBubble({ message, pdfOpen, onNavigate }: MessageBubbleProps) {
  const isUser = message.role === "user"

  return (
    <div
      className={cn(
        "msg-enter flex flex-col gap-1",
        isUser ? "items-end" : "items-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-sm px-3.5 py-2.5 text-sm leading-relaxed",
          isUser
            ? "rounded-br-xs"
            : "rounded-bl-xs"
        )}
        style={{
          backgroundColor: isUser ? "var(--surface-2)" : "var(--surface)",
          color: "var(--ink)",
          border: "1px solid var(--se-border)",
        }}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none [&_a]:text-[var(--se-accent)] [&_code]:rounded-xs [&_code]:bg-[var(--surface-2)] [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-xs [&_pre]:rounded-sm [&_pre]:bg-[var(--surface-2)] [&_pre]:p-3 [&_strong]:font-semibold">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>

      {/* Slide navigation chip — only shown when viewer is open OR just opened */}
      {!isUser && message.uiAction && (
        <SlideChip
          page={message.uiAction.page}
          visible={pdfOpen}
          onClick={() =>
            onNavigate(
              message.uiAction!.course,
              message.uiAction!.topic,
              message.uiAction!.page
            )
          }
        />
      )}
    </div>
  )
}
