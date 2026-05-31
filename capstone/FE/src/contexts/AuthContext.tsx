"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react"
import { useRouter } from "next/navigation"
import { createApiClient } from "@/lib/api"

type Language = "vn" | "eng"

interface AuthState {
  accessToken: string | null
  isAdmin: boolean
  language: Language
  sessionId: string | null
}

interface AuthContextValue extends AuthState {
  login: (token: string, isAdmin: boolean) => void
  logout: () => Promise<void>
  setLanguage: (lang: Language) => void
  setSessionId: (id: string) => void
  apiFetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [state, setState] = useState<AuthState>({
    accessToken: null,
    isAdmin: false,
    language: "vn",
    sessionId: null,
  })

  // tokenRef keeps apiFetch closures from going stale when accessToken changes
  const tokenRef = useRef<string | null>(null)
  tokenRef.current = state.accessToken

  const handleAuthFailure = useCallback(() => {
    setState({ accessToken: null, isAdmin: false, language: "vn", sessionId: null })
    tokenRef.current = null
    router.push("/login")
  }, [router])

  const handleTokenRefresh = useCallback((newToken: string) => {
    tokenRef.current = newToken
    setState((s) => ({ ...s, accessToken: newToken }))
  }, [])

  const { apiFetch } = createApiClient(
    () => tokenRef.current,
    handleTokenRefresh,
    handleAuthFailure
  )

  const login = useCallback((token: string, isAdmin: boolean) => {
    setState((s) => ({ ...s, accessToken: token, isAdmin }))
  }, [])

  const logout = useCallback(async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" })
    } catch {
      // best-effort
    }
    setState({ accessToken: null, isAdmin: false, language: "vn", sessionId: null })
    tokenRef.current = null
    router.push("/login")
  }, [router])

  const setLanguage = useCallback((lang: Language) => {
    setState((s) => ({ ...s, language: lang }))
  }, [])

  const setSessionId = useCallback((id: string) => {
    setState((s) => ({ ...s, sessionId: id }))
  }, [])

  // On mount: try to restore session via the httpOnly refresh cookie
  useEffect(() => {
    async function restore() {
      try {
        const res = await fetch("/api/auth/refresh", { method: "POST" })
        if (!res.ok) return
        const data = await res.json()
        const token: string = data.access_token
        const isAdmin: boolean = data.is_admin ?? false
        setState((s) => ({ ...s, accessToken: token, isAdmin }))
        tokenRef.current = token

        // Load language preference
        const profile = await fetch("/api/profile", {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (profile.ok) {
          const p = await profile.json()
          if (p.language) setState((s) => ({ ...s, language: p.language }))
        }
      } catch {
        // No valid session — stay logged out
      }
    }
    restore()
  }, [])

  return (
    <AuthContext.Provider
      value={{ ...state, login, logout, setLanguage, setSessionId, apiFetch }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>")
  return ctx
}
