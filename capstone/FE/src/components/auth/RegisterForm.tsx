"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"

export function RegisterForm() {
  const router = useRouter()
  const [studentId, setStudentId] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function validate(): string | null {
    if (studentId.trim().length < 3) return "Mã sinh viên phải có ít nhất 3 ký tự."
    if (password.length < 6) return "Mật khẩu phải có ít nhất 6 ký tự."
    if (password !== confirm) return "Mật khẩu xác nhận không khớp."
    return null
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }

    setError(null)
    setLoading(true)

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId, password }),
      })
      const data = await res.json()

      if (res.status === 409) {
        setError("Mã sinh viên này đã được sử dụng. Hãy chọn mã khác hoặc đăng nhập.")
        return
      }

      if (!res.ok) {
        setError(data.detail ?? "Đăng ký thất bại. Vui lòng thử lại.")
        return
      }

      toast.success("Tài khoản đã được tạo thành công!", {
        description: "Bạn có thể đăng nhập ngay bây giờ.",
      })
      // delay so Sonner mounts the toast before React navigates away
      setTimeout(() => router.push("/login"), 1500)
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
          htmlFor="reg-id"
          className="block text-sm font-medium"
          style={{ color: "var(--ink)" }}
        >
          Mã sinh viên
        </label>
        <Input
          id="reg-id"
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
          htmlFor="reg-pw"
          className="block text-sm font-medium"
          style={{ color: "var(--ink)" }}
        >
          Mật khẩu
        </label>
        <Input
          id="reg-pw"
          type="password"
          autoComplete="new-password"
          placeholder="Ít nhất 6 ký tự"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
        />
      </div>

      <div className="space-y-1.5">
        <label
          htmlFor="reg-confirm"
          className="block text-sm font-medium"
          style={{ color: "var(--ink)" }}
        >
          Xác nhận mật khẩu
        </label>
        <Input
          id="reg-confirm"
          type="password"
          autoComplete="new-password"
          placeholder="••••••••"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
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
        Tạo tài khoản
      </Button>

      <p
        className="text-center text-sm"
        style={{ color: "var(--ink-muted)" }}
      >
        Đã có tài khoản?{" "}
        <Link
          href="/login"
          className="font-medium transition-colors hover:underline"
          style={{ color: "var(--se-accent)" }}
        >
          Đăng nhập
        </Link>
      </p>
    </form>
  )
}
