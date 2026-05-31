"use client"

import { useAuth } from "@/contexts/AuthContext"
import { IngestForm } from "@/components/ingest/IngestForm"
import { TopBar } from "@/components/layout/TopBar"

export default function AdminIngestPage() {
  const { isAdmin } = useAuth()

  if (!isAdmin) {
    return (
      <div
        className="flex min-h-dvh flex-col items-center justify-center gap-2"
        style={{ backgroundColor: "var(--bg)" }}
      >
        <p className="text-sm font-medium" style={{ color: "var(--ink)" }}>
          Truy cập bị từ chối
        </p>
        <p className="text-xs" style={{ color: "var(--ink-muted)" }}>
          Trang này chỉ dành cho quản trị viên.
        </p>
      </div>
    )
  }

  return (
    <div className="flex min-h-dvh flex-col" style={{ backgroundColor: "var(--bg)" }}>
      <TopBar title="Nạp tài liệu" />

      <main className="flex flex-1 gap-8 px-8 py-10">
        {/* Left: form */}
        <div className="flex-1 max-w-xl space-y-4">
          <div>
            <h1
              className="text-2xl font-semibold"
              style={{ color: "var(--ink)" }}
            >
              Nạp tài liệu khóa học
            </h1>
            <p
              className="mt-1 text-sm"
              style={{ color: "var(--ink-muted)" }}
            >
              Tải lên slides và giáo trình PDF. Sau khi upload, hệ thống sẽ xử lý tự động.
            </p>
          </div>

          <IngestForm />
        </div>

        {/* Right: info panel */}
        <aside
          className="hidden w-72 shrink-0 rounded-md p-6 lg:block"
          style={{
            backgroundColor: "var(--surface)",
            border: "1px solid var(--se-border)",
          }}
        >
          <h2
            className="mb-3 text-sm font-semibold"
            style={{ color: "var(--ink)" }}
          >
            Lưu ý
          </h2>
          <ul
            className="space-y-2 text-xs leading-relaxed"
            style={{ color: "var(--ink-muted)" }}
          >
            <li>Chỉ hỗ trợ file <code>.pdf</code>.</li>
            <li>Tên môn học sẽ được dùng làm prefix trong storage. Không dùng ký tự đặc biệt.</li>
            <li>Quá trình nạp dữ liệu chạy nền. Theo dõi tiến trình trong server log.</li>
            <li>Nạp lại sẽ <strong>reset</strong> toàn bộ dữ liệu của môn học đó.</li>
          </ul>
        </aside>
      </main>
    </div>
  )
}
