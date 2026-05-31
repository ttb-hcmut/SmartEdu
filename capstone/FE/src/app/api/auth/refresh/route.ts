import { NextResponse } from "next/server"
import { cookies } from "next/headers"

const API = process.env.BACKEND_URL ?? "http://localhost:5000"

export async function POST() {
  const cookieStore = await cookies()
  const refreshToken = cookieStore.get("refresh_token")?.value

  if (!refreshToken) {
    return NextResponse.json({ detail: "No refresh token" }, { status: 401 })
  }

  let upstream: Response
  try {
    upstream = await fetch(`${API}/system/v0/student/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
  } catch {
    cookieStore.delete("refresh_token")
    return NextResponse.json({ detail: "Service unavailable" }, { status: 503 })
  }

  if (!upstream.ok) {
    cookieStore.delete("refresh_token")
    return NextResponse.json({ detail: "Refresh failed" }, { status: 401 })
  }

  const data = await upstream.json()
  const { access_token, refresh_token: newRefresh, is_admin } = data

  // Rotate the cookie if a new refresh token was issued
  if (newRefresh) {
    cookieStore.set("refresh_token", newRefresh, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 7200,
    })
  }

  return NextResponse.json({ access_token, is_admin })
}
