"use client"

import { useCallback, useRef, useState } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { normaliseUiAction, type UiAction } from "@/lib/normalise"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000"
const INTERVALS = [3_000, 5_000, 10_000] // ms — escalating poll cadence
const TIMEOUT_MS = 300_000               // 5 min hard timeout

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
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const startTimeRef = useRef<number>(0)

  function clearTimer() {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = null
  }

  const poll = useCallback(
    async (taskId: string, attemptIdx: number) => {
      if (Date.now() - startTimeRef.current >= TIMEOUT_MS) {
        setState("timeout")
        return
      }

      try {
        const res = await apiFetch(
          `${API}/system/v0/ta/chat/status/${taskId}`
        )
        if (!res.ok) {
          setState("fail")
          setError(`Server responded with ${res.status}`)
          return
        }

        const data = await res.json()

        if (data.status === "working") {
          if (data.agent_name || data.thought) {
            setThought({
              agentName: data.agent_name,
              intent: data.intent,
              thought: data.thought,
            })
          }
          const delay = INTERVALS[Math.min(attemptIdx, INTERVALS.length - 1)]
          timerRef.current = setTimeout(() => poll(taskId, attemptIdx + 1), delay)
          return
        }

        if (data.status === "finished" || data.result) {
          const r = data.result ?? data
          const message: string = r.message || r.summary || ""
          if (!message) {
            setState("fail")
            setError("Trợ lý không tạo được câu trả lời. Vui lòng thử lại.")
            return
          }
          setResult({
            message,
            uiAction: normaliseUiAction(r.ui_action ?? null),
          })
          setThought(null)
          setState("done")
          return
        }

        if (data.status === "Fail" || data.status === "failed") {
          setState("fail")
          setError(data.error ?? "TA workflow failed.")
          return
        }

        // Unknown status — keep polling
        const delay = INTERVALS[Math.min(attemptIdx, INTERVALS.length - 1)]
        timerRef.current = setTimeout(() => poll(taskId, attemptIdx + 1), delay)
      } catch (err) {
        setState("fail")
        setError(err instanceof Error ? err.message : "Polling error")
      }
    },
    [apiFetch]
  )

  const submit = useCallback(
    async (userInput: string) => {
      if (!sessionId) return
      clearTimer()
      setState("polling")
      setResult(null)
      setError(null)
      setThought(null)
      startTimeRef.current = Date.now()

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
        // First poll after the initial interval
        timerRef.current = setTimeout(() => poll(task_id, 0), INTERVALS[0])
      } catch (err) {
        setState("fail")
        setError(err instanceof Error ? err.message : "Failed to send message")
      }
    },
    [apiFetch, sessionId, language, poll]
  )

  function reset() {
    clearTimer()
    setState("idle")
    setResult(null)
    setError(null)
    setThought(null)
  }

  return { state, result, error, thought, submit, reset }
}
