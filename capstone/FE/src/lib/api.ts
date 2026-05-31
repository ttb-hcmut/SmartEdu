/**
 * createApiClient — wraps fetch with Bearer auth + 401 auto-refresh.
 *
 * Security contract:
 *   - Access token is read via getToken() on every call (never captured at
 *     construction time) so the closure never goes stale.
 *   - On 401, a single POST /api/auth/refresh attempt is made. If it
 *     succeeds, onTokenRefresh is called and the original request is retried
 *     exactly once. If it fails, onAuthFailure is called (clears context +
 *     redirects to /login) and an error is thrown.
 */

type GetToken = () => string | null
type OnTokenRefresh = (newToken: string) => void
type OnAuthFailure = () => void

export interface ApiClient {
  apiFetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
}

export function createApiClient(
  getToken: GetToken,
  onTokenRefresh: OnTokenRefresh,
  onAuthFailure: OnAuthFailure
): ApiClient {
  async function tryRefresh(): Promise<string | null> {
    const res = await fetch("/api/auth/refresh", { method: "POST" })
    if (!res.ok) return null
    const data = await res.json()
    return data.access_token ?? null
  }

  function buildInit(init: RequestInit | undefined, token: string | null): RequestInit {
    const headers = new Headers(init?.headers)
    if (token) headers.set("Authorization", `Bearer ${token}`)
    return { ...init, headers }
  }

  async function apiFetch(
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> {
    const token = getToken()
    const res = await fetch(input, buildInit(init, token))

    if (res.status !== 401) return res

    // First 401 — attempt refresh
    const newToken = await tryRefresh()
    if (!newToken) {
      onAuthFailure()
      throw new Error("Session expired. Please log in again.")
    }

    onTokenRefresh(newToken)

    // Retry once with the new token
    const retry = await fetch(input, buildInit(init, newToken))
    if (retry.status === 401) {
      onAuthFailure()
      throw new Error("Session expired. Please log in again.")
    }
    return retry
  }

  return { apiFetch }
}
