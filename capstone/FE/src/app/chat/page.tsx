"use client"

import { useCallback, useEffect, useState } from "react"
import dynamic from "next/dynamic"
import { AppShell } from "@/components/layout/AppShell"
import { Sidebar } from "@/components/layout/Sidebar"
import { TopBar } from "@/components/layout/TopBar"
import { ChatPanel } from "@/components/chat/ChatPanel"
import { PDFSkeleton } from "@/components/pdf/PDFSkeleton"
import { useSession } from "@/hooks/useSession"
import { useAuth } from "@/contexts/AuthContext"
import { type UiAction } from "@/lib/normalise"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000"

// SSR disabled — PDFViewer uses pdfjs-dist which requires browser APIs
const PDFViewer = dynamic(
  () => import("@/components/pdf/PDFViewer").then((m) => m.PDFViewer),
  { ssr: false, loading: () => <PDFSkeleton /> }
)

export default function ChatPage() {
  useSession()
  const { apiFetch } = useAuth()

  const [courses, setCourses] = useState<string[]>([])
  const [activeCourse, setActiveCourse] = useState<string | null>(null)
  const [openCourse, setOpenCourse] = useState<string | null>(null)
  const [openTopic, setOpenTopic] = useState<string | null>(null)
  const [pdfPage, setPdfPage] = useState<number>(1)

  // Fetch available courses on mount
  useEffect(() => {
    apiFetch(`${API}/system/v0/knowledge/courses`)
      .then((r) => r.json())
      .then((data) => {
        const list: string[] = data.courses ?? data ?? []
        setCourses(list)
        if (list.length > 0) setActiveCourse(list[0])
      })
      .catch(() => {})
  }, [apiFetch])

  const handleUiAction = useCallback((action: UiAction) => {
    if (!openCourse || !openTopic) {
      // Cold start — open viewer at the referenced topic
      setOpenCourse(action.course)
      setOpenTopic(action.topic)
      setPdfPage(action.page)
    } else {
      // Viewer already open — just navigate to the new page
      setPdfPage(action.page)
      // If topic changed, update it
      if (action.topic && action.topic !== openTopic) {
        setOpenCourse(action.course)
        setOpenTopic(action.topic)
      }
    }
  }, [openCourse, openTopic])

  const pdfOpen = !!(openCourse && openTopic)

  return (
    <AppShell
      sidebar={
        <Sidebar
          courses={courses}
          activeCourse={activeCourse}
          onCourseSelect={(c) => {
            setActiveCourse(c)
            setOpenCourse(c)
            setOpenTopic(null)
            setPdfPage(1)
          }}
        />
      }
      panel={
        pdfOpen ? (
          <PDFViewer
            course={openCourse!}
            topic={openTopic!}
            page={pdfPage}
            onPageChange={setPdfPage}
            className="h-full"
          />
        ) : undefined
      }
    >
      <TopBar title={activeCourse ?? "Trò chuyện"} />
      <ChatPanel pdfOpen={pdfOpen} onUiAction={handleUiAction} />
    </AppShell>
  )
}
