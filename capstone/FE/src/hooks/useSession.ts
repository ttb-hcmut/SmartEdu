"use client"

import { useEffect, useRef } from "react"
import { useAuth } from "@/contexts/AuthContext"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000"

export function useSession() {
  const { apiFetch, accessToken, setSessionId } = useAuth()
  const tokenRef = useRef<string | null>(null)
  const sessionIdRef = useRef<string | null>(null)

  // Keep a stable ref to the current token for the cleanup fetch
  tokenRef.current = accessToken

  useEffect(() => {
    let mounted = true

    async function start() {
      try {
        const res = await apiFetch(`${API}/system/v0/student/session/start`, {
          method: "POST",
        })
        if (res.ok && mounted) {
          const data = await res.json()
          sessionIdRef.current = data.session_id
          setSessionId(data.session_id)
        }
      } catch {
        // Non-fatal — session tracking unavailable
      }
    }

    start()

    return () => {
      mounted = false
      // keepalive: true fires the DELETE even when the page is unloading
      if (sessionIdRef.current && tokenRef.current) {
        fetch(`${API}/system/v0/student/session/end`, {
          method: "DELETE",
          keepalive: true,
          headers: { Authorization: `Bearer ${tokenRef.current}` },
        }).catch(() => {})
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}
