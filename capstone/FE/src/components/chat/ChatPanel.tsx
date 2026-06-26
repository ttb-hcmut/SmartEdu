"use client"

import { useCallback, useState } from "react"
import { toast } from "sonner"
import { v7 as uuid } from "uuid"
import { MessageList } from "./MessageList"
import { MessageInput } from "./MessageInput"
import { useChatPoll } from "@/hooks/useChatPoll"
import { type UiAction } from "@/lib/normalise"
import { type Message } from "./MessageBubble"

interface ChatPanelProps {
  pdfOpen: boolean
  onUiAction: (action: UiAction) => void
}

export function ChatPanel({ pdfOpen, onUiAction }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const { state, result, error, thought, partial, submit, reset } = useChatPoll()

  const handleSubmit = useCallback(
    async (userInput: string) => {
      // Optimistic user message
      const userMsg: Message = {
        id: uuid(),
        role: "user",
        content: userInput,
      }
      setMessages((prev) => [...prev, userMsg])

      await submit(userInput)
    },
    [submit]
  )

  // Append TA result when polling completes
  const prevStateRef = useState<typeof state>("idle")
  if (state === "done" && result && prevStateRef[0] !== "done") {
    prevStateRef[1]("done")
    const taMsg: Message = {
      id: uuid(),
      role: "ta",
      content: result.message,
      uiAction: result.uiAction ?? undefined,
    }
    setMessages((prev) => [...prev, taMsg])
    if (result.uiAction) {
      onUiAction(result.uiAction)
    }
    reset()
  } else if (state === "idle" && prevStateRef[0] === "done") {
    prevStateRef[1]("idle")
  } else if (
    (state === "fail" || state === "timeout") &&
    prevStateRef[0] !== "fail" &&
    prevStateRef[0] !== "timeout"
  ) {
    prevStateRef[1](state)
    toast.error("Trợ lý gặp lỗi", { description: error ?? undefined })
  } else if (state === "polling" && prevStateRef[0] !== "polling") {
    prevStateRef[1]("polling")
  }

  const handleNavigate = useCallback(
    (course: string, topic: string, page: number) => {
      onUiAction({ action: "NAVIGATE_PDF", course, topic, destination: "", page })
    },
    [onUiAction]
  )

  return (
    <div
      className="flex h-full flex-col"
      style={{ backgroundColor: "var(--bg)" }}
    >
      <MessageList
        messages={messages}
        pollState={state}
        thought={thought}
        partial={partial}
        error={error}
        pdfOpen={pdfOpen}
        onNavigate={handleNavigate}
      />
      <MessageInput onSubmit={handleSubmit} pollState={state} />
    </div>
  )
}
