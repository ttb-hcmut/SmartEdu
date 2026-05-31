import { NextRequest, NextResponse } from "next/server"

const API = process.env.BACKEND_URL ?? "http://localhost:5000"

export async function POST(req: NextRequest) {
  const body = await req.json()

  let upstream: Response
  try {
    upstream = await fetch(`${API}/system/v0/student/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
  } catch {
    return NextResponse.json(
      { detail: "Service temporarily unavailable" },
      { status: 503 }
    )
  }

  const data = await upstream.json().catch(() => ({}))
  return NextResponse.json(data, { status: upstream.status })
}
