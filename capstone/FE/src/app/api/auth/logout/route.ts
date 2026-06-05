import { NextResponse } from "next/server"

export async function POST() {
  const res = new NextResponse(null, { status: 204 })
  res.cookies.delete("refresh_token")
  return res
}
