"use client"

import { useCallback, useRef, useState } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { normaliseUiAction, type UiAction } from "@/lib/normalise"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000"

export type PollState = "idle" | "polling" | "done" | "fail" | "timeout"

export interface PollResult {
  message: string
  uiAction: UiAction | null
}

export interface AgentThought {
  agentName?: string
  intent?: string
  thought?: string
}

export function useChatPoll() {
  const { apiFetch, sessionId, language } = useAuth()
  const [state, setState] = useState<PollState>("idle")
  const [result, setResult] = useState<PollResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [thought, setThought] = useState<AgentThought | null>(null)
  const [partial, setPartial] = useState<string>("") // live answer text as tokens stream
  const abortRef = useRef<AbortController | null>(null)

  const reset = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setState("idle")
    setResult(null)
    setError(null)
    setThought(null)
    setPartial("")
  }, [])

  const streamTask = useCallback(
    async (taskId: string) => {
      const ctrl = new AbortController()
      abortRef.current = ctrl
      let acc = ""

      try {
        const res = await apiFetch(`${API}/system/v0/ta/chat/stream/${taskId}`, {
          signal: ctrl.signal,
          headers: { Accept: "text/event-stream" },
        })
        if (!res.ok || !res.body) {
          setState("fail")
          setError(`Stream failed (${res.status})`)
          return
        }

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buf = ""

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buf += decoder.decode(value, { stream: true })

          // SSE frames are separated by a blank line
          let sep
          while ((sep = buf.indexOf("\n\n")) !== -1) {
            const frame = buf.slice(0, sep)
            buf = buf.slice(sep + 2)
            const line = frame.split("\n").find((l) => l.startsWith("data:"))
            if (!line) continue

            const evt = JSON.parse(line.slice(5).trim())
            if (evt.type === "step") {
              setThought({ thought: evt.label, agentName: "TA Agent" })
            } else if (evt.type === "token") {
              acc += evt.text
              setPartial(acc)
            } else if (evt.type === "done") {
              setResult({
                message: evt.message ?? acc,
                uiAction: normaliseUiAction(evt.ui_action ?? null),
              })
              setThought(null)
              setState("done")
              return
            } else if (evt.type === "error") {
              setState("fail")
              setError(evt.error ?? "TA workflow failed.")
              return
            }
          }
        }

        // Stream closed without a terminal event — salvage accumulated text
        if (acc) {
          setResult({ message: acc, uiAction: null })
          setThought(null)
          setState("done")
        } else {
          setState("fail")
          setError("Stream ended unexpectedly.")
        }
      } catch (err) {
        if ((err as Error)?.name === "AbortError") return
        setState("fail")
        setError(err instanceof Error ? err.message : "Streaming error")
      }
    },
    [apiFetch]
  )

  const submit = useCallback(
    async (userInput: string) => {
      if (!sessionId) return
      abortRef.current?.abort()
      setState("polling")
      setResult(null)
      setError(null)
      setThought(null)
      setPartial("")

      try {
        const res = await apiFetch(`${API}/system/v0/ta/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            user_input: userInput,
            language,
          }),
        })

        if (!res.ok) {
          setState("fail")
          setError(`Could not reach TA (${res.status})`)
          return
        }

        const { task_id } = await res.json()
        await streamTask(task_id)
      } catch (err) {
        setState("fail")
        setError(err instanceof Error ? err.message : "Failed to send message")
      }
    },
    [apiFetch, sessionId, language, streamTask]
  )

  return { state, result, error, thought, partial, submit, reset }
}
