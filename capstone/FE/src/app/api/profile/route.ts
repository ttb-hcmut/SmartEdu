import { NextRequest, NextResponse } from "next/server"

const API = process.env.BACKEND_URL ?? "http://localhost:5000"

async function forwardWithAuth(req: NextRequest, method: string, body?: string) {
  const authHeader = req.headers.get("authorization")
  if (!authHeader) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 })
  }

  let upstream: Response
  try {
    upstream = await fetch(`${API}/system/v0/student/profile`, {
      method,
      headers: {
        Authorization: authHeader,
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      ...(body ? { body } : {}),
    })
  } catch {
    return NextResponse.json({ detail: "Service unavailable" }, { status: 503 })
  }

  const data = await upstream.json().catch(() => ({}))
  return NextResponse.json(data, { status: upstream.status })
}

export async function GET(req: NextRequest) {
  return forwardWithAuth(req, "GET")
}

export async function PATCH(req: NextRequest) {
  const body = await req.text()
  return forwardWithAuth(req, "PATCH", body)
}
