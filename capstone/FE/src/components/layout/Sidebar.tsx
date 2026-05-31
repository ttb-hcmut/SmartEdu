"use client"

import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { LogOut, Settings, BookOpen, ChevronRight } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"

interface SidebarProps {
  courses?: string[]
  activeCourse?: string | null
  onCourseSelect?: (course: string) => void
  sessionId?: string | null
}

export function Sidebar({
  courses = [],
  activeCourse = null,
  onCourseSelect,
  sessionId,
}: SidebarProps) {
  const { logout } = useAuth()

  return (
    <div className="flex h-full flex-col">
      {/* Brand */}
      <div
        className="flex h-14 shrink-0 items-center px-4 border-b"
        style={{ borderColor: "var(--se-border)" }}
      >
        <span
          className="text-sm font-semibold tracking-tight"
          style={{ color: "var(--se-primary)" }}
        >
          SmartEdu
        </span>
        {sessionId && (
          <span
            className="ml-auto size-2 rounded-full thought-pulse"
            style={{ backgroundColor: "var(--se-primary)" }}
            title="Phiên học đang hoạt động"
          />
        )}
      </div>

      {/* Course list */}
      <nav className="flex-1 overflow-y-auto p-2">
        {courses.length > 0 && (
          <>
            <p
              className="mb-1 px-2 py-1 text-[11px] font-medium uppercase tracking-widest"
              style={{ color: "var(--ink-muted)" }}
            >
              Môn học
            </p>
            <ul className="space-y-0.5">
              {courses.map((course) => (
                <li key={course}>
                  <button
                    onClick={() => onCourseSelect?.(course)}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm transition-colors",
                      activeCourse === course
                        ? "font-medium"
                        : "hover:bg-[var(--se-accent-subtle)]"
                    )}
                    style={{
                      backgroundColor:
                        activeCourse === course ? "var(--se-accent-subtle)" : undefined,
                      color: activeCourse === course ? "var(--ink)" : "var(--ink-muted)",
                    }}
                  >
                    <BookOpen className="size-3.5 shrink-0" />
                    <span className="truncate">{course}</span>
                    {activeCourse === course && (
                      <ChevronRight className="ml-auto size-3 shrink-0" />
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}

        {courses.length === 0 && (
          <p
            className="mt-4 px-2 text-xs"
            style={{ color: "var(--ink-muted)" }}
          >
            Chưa có môn học nào.
          </p>
        )}
      </nav>

      {/* Footer actions */}
      <div
        className="shrink-0 border-t p-2 space-y-1"
        style={{ borderColor: "var(--se-border)" }}
      >
        <Link
          href="/settings"
          className="flex h-7 w-full items-center gap-2 rounded-sm px-3 text-sm transition-colors hover:bg-[var(--se-accent-subtle)]"
          style={{ color: "var(--ink-muted)" }}
        >
          <Settings className="size-3.5" />
          Cài đặt
        </Link>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2"
          onClick={() => logout()}
          style={{ color: "var(--ink-muted)" }}
        >
          <LogOut className="size-3.5" />
          Đăng xuất
        </Button>
      </div>
    </div>
  )
}
