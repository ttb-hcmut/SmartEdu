import { NextResponse } from "next/server"
import { cookies } from "next/headers"

export async function POST() {
  const cookieStore = await cookies()
  cookieStore.delete("refresh_token")
  return new NextResponse(null, { status: 204 })
}
