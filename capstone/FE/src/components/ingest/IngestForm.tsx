"use client"

import { useState } from "react"
import { toast } from "sonner"
import { FileDropzone } from "./FileDropzone"
import { UploadProgress, type FileProgress } from "./UploadProgress"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useAuth } from "@/contexts/AuthContext"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000"

export function IngestForm() {
  const { apiFetch } = useAuth()
  const [courseName, setCourseName] = useState("")
  const [slides, setSlides] = useState<File[]>([])
  const [textbooks, setTextbooks] = useState<File[]>([])
  const [progress, setProgress] = useState<FileProgress[]>([])
  const [submitting, setSubmitting] = useState(false)

  function updateProgress(name: string, patch: Partial<FileProgress>) {
    setProgress((prev) =>
      prev.map((f) => (f.name === name ? { ...f, ...patch } : f))
    )
  }

  async function uploadFile(file: File, url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open("PUT", url)
      xhr.setRequestHeader("Content-Type", "application/pdf")

      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100)
          updateProgress(file.name, { progress: pct })
        }
      })

      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          updateProgress(file.name, { status: "done", progress: 100 })
          resolve()
        } else {
          updateProgress(file.name, { status: "error", error: `HTTP ${xhr.status}` })
          reject(new Error(`Upload failed: ${xhr.status}`))
        }
      })

      xhr.addEventListener("error", () => {
        updateProgress(file.name, { status: "error", error: "Network error" })
        reject(new Error("Network error"))
      })

      xhr.send(file)
    })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!courseName.trim()) return
    const allFiles = [...slides, ...textbooks]
    if (allFiles.length === 0) {
      toast.error("Vui lòng thêm ít nhất một file PDF.")
      return
    }

    setSubmitting(true)
    setProgress(
      allFiles.map((f) => ({ name: f.name, status: "pending", progress: 0 }))
    )

    try {
      // Step 1: Get presigned upload URLs
      const urlRes = await apiFetch(`${API}/system/v0/knowledge/upload-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_name: courseName.trim(),
          file_names: allFiles.map((f) => f.name),
        }),
      })
      if (!urlRes.ok) throw new Error(`Failed to get upload URLs (${urlRes.status})`)
      const { targets } = await urlRes.json()

      // Step 2: Upload each file directly to MinIO
      setProgress((prev) =>
        prev.map((f) => ({ ...f, status: "uploading" as const }))
      )
      const fileMap = new Map(allFiles.map((f) => [f.name, f]))
      await Promise.all(
        (targets as { name: string; url: string }[]).map(({ name, url }) => {
          const file = fileMap.get(name)
          if (!file) return Promise.resolve()
          return uploadFile(file, url)
        })
      )

      // Step 3: Trigger ingestion
      const ingestRes = await apiFetch(`${API}/system/v0/knowledge/ingest-course`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_name: courseName.trim(),
          slide_files: slides.map((f) => f.name),
          textbook_files: textbooks.map((f) => f.name),
          reset: true,
        }),
      })
      if (!ingestRes.ok) throw new Error(`Ingest failed (${ingestRes.status})`)

      toast.success("Đang xử lý tài liệu", {
        description: "Quá trình nạp dữ liệu đang chạy nền. Kiểm tra server log để theo dõi.",
        duration: 8000,
      })
      setCourseName("")
      setSlides([])
      setTextbooks([])
      setProgress([])
    } catch (err) {
      toast.error("Nạp dữ liệu thất bại", {
        description: err instanceof Error ? err.message : "Lỗi không xác định",
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-1.5">
        <label
          htmlFor="course-name"
          className="block text-sm font-medium"
          style={{ color: "var(--ink)" }}
        >
          Tên môn học
        </label>
        <Input
          id="course-name"
          placeholder="VD: MachineLearning"
          value={courseName}
          onChange={(e) => setCourseName(e.target.value)}
          required
          disabled={submitting}
        />
      </div>

      <FileDropzone
        label="Slides (PDF)"
        files={slides}
        onFilesChange={setSlides}
      />

      <FileDropzone
        label="Giáo trình (PDF)"
        files={textbooks}
        onFilesChange={setTextbooks}
      />

      {progress.length > 0 && (
        <UploadProgress files={progress} />
      )}

      <Button
        type="submit"
        className="w-full"
        disabled={submitting || !courseName.trim()}
      >
        {submitting && <Spinner size="sm" className="mr-1.5" />}
        {submitting ? "Đang tải lên…" : "Nạp tài liệu"}
      </Button>
    </form>
  )
}
