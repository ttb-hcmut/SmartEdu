"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"

export function LoginForm() {
  const router = useRouter()
  const auth = useAuth()
  const [studentId, setStudentId] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId, password }),
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail ?? "Đăng nhập thất bại. Vui lòng thử lại.")
        return
      }

      auth.login(data.access_token, data.is_admin ?? false)

      // Non-critical: load language preference
      try {
        const profile = await fetch("/api/profile", {
          headers: { Authorization: `Bearer ${data.access_token}` },
        })
        if (profile.ok) {
          const p = await profile.json()
          if (p.language) auth.setLanguage(p.language)
        }
      } catch { /* best-effort */ }

      router.push("/chat")
    } catch {
      setError("Không thể kết nối đến máy chủ. Vui lòng thử lại.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <label
          htmlFor="login-id"
          className="block text-sm font-medium"
          style={{ color: "var(--ink)" }}
        >
          Mã sinh viên
        </label>
        <Input
          id="login-id"
          type="text"
          autoComplete="username"
          placeholder="VD: SV123456"
          value={studentId}
          onChange={(e) => setStudentId(e.target.value)}
          required
          disabled={loading}
        />
      </div>

      <div className="space-y-1.5">
        <label
          htmlFor="login-pw"
          className="block text-sm font-medium"
          style={{ color: "var(--ink)" }}
        >
          Mật khẩu
        </label>
        <Input
          id="login-pw"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
        />
      </div>

      {error && (
        <p className="text-sm" style={{ color: "var(--error)" }} role="alert">
          {error}
        </p>
      )}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading && <Spinner size="sm" className="mr-1.5" />}
        Đăng nhập
      </Button>

      <p
        className="text-center text-sm"
        style={{ color: "var(--ink-muted)" }}
      >
        Chưa có tài khoản?{" "}
        <Link
          href="/register"
          className="font-medium transition-colors hover:underline"
          style={{ color: "var(--se-accent)" }}
        >
          Đăng ký ngay
        </Link>
      </p>
    </form>
  )
}
