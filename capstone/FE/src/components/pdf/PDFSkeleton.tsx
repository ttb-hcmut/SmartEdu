"use client"

import { cn } from "@/lib/utils"

export function PDFSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("flex flex-col gap-3 p-6", className)}
      aria-busy="true"
      aria-label="Đang tải PDF"
    >
      {/* Page header placeholder */}
      <div className="pdf-shimmer h-5 w-1/3 rounded-xs" />

      {/* Page body blocks */}
      <div className="pdf-shimmer h-64 w-full rounded-xs" />
      <div className="pdf-shimmer h-3 w-full rounded-xs" />
      <div className="pdf-shimmer h-3 w-5/6 rounded-xs" />
      <div className="pdf-shimmer h-3 w-4/6 rounded-xs" />
      <div className="pdf-shimmer mt-2 h-32 w-full rounded-xs" />
      <div className="pdf-shimmer h-3 w-full rounded-xs" />
      <div className="pdf-shimmer h-3 w-3/4 rounded-xs" />
    </div>
  )
}
