import { NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

const API = process.env.BACKEND_URL ?? "http://localhost:5000"

export async function POST(req: NextRequest) {
  const { student_id, password } = await req.json()

  // FastAPI OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
  // with the field named "username" (not "student_id")
  const body = new URLSearchParams({
    username: student_id,
    password,
  })

  let upstream: Response
  try {
    upstream = await fetch(`${API}/system/v0/student/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    })
  } catch {
    return NextResponse.json(
      { detail: "Service temporarily unavailable" },
      { status: 503 }
    )
  }

  if (!upstream.ok) {
    const err = await upstream.json().catch(() => ({ detail: "Login failed" }))
    return NextResponse.json(err, { status: upstream.status })
  }

  const data = await upstream.json()
  const { access_token, refresh_token, is_admin } = data

  const cookieStore = await cookies()
  cookieStore.set("refresh_token", refresh_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 7200, // 2 hours
  })

  // Never return refresh_token to the browser
  return NextResponse.json({ access_token, is_admin })
}
