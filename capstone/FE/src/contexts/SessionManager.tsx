"use client"
import { useEffect, useRef } from "react"
import { useAuth } from "@/contexts/AuthContext"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000"

export function SessionManager({ children }: { children: React.ReactNode }) {
  const { apiFetch, accessToken, setSessionId } = useAuth()

  const sessionIdRef = useRef<string | null>(null)
  const tokenRef     = useRef<string | null>(null)
  const prevTokenRef = useRef<string | null>(null)
  const startedRef   = useRef(false)

  // always current — read inside event listener closures
  tokenRef.current = accessToken

  // start once when first authenticated
  useEffect(() => {
    if (!accessToken || startedRef.current) return
    startedRef.current = true

    let mounted = true
    async function start() {
      try {
        const res = await apiFetch(`${API}/system/v0/student/session/start`, { method: "POST" })
        if (res.ok && mounted) {
          const data = await res.json()
          sessionIdRef.current = data.session_id
          setSessionId(data.session_id)
        }
      } catch {}
    }
    start()
    return () => { mounted = false }
  }, [accessToken, apiFetch, setSessionId])

  // end on tab/window close only
  useEffect(() => {
    function sendEnd() {
      if (!sessionIdRef.current || !tokenRef.current) return
      fetch(`${API}/system/v0/student/session/end?session_id=${sessionIdRef.current}`, {
        method: "DELETE",
        keepalive: true,
        headers: { Authorization: `Bearer ${tokenRef.current}` },
      }).catch(() => {})
    }
    window.addEventListener("beforeunload", sendEnd)
    return () => window.removeEventListener("beforeunload", sendEnd)
  }, [])

  // end on logout (accessToken → null)
  useEffect(() => {
    if (accessToken !== null) {
      prevTokenRef.current = accessToken
      return
    }
    const lastToken = prevTokenRef.current
    if (sessionIdRef.current && lastToken) {
      fetch(`${API}/system/v0/student/session/end?session_id=${sessionIdRef.current}`, {
        method: "DELETE",
        keepalive: true,
        headers: { Authorization: `Bearer ${lastToken}` },
      }).catch(() => {})
      sessionIdRef.current = null
      setSessionId(null)
    }
    prevTokenRef.current = null
    startedRef.current = false  // allow re-start after re-login
  }, [accessToken, setSessionId])

  return <>{children}</>
}
