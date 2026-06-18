"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { listChunks, fetchExportData } from "@/lib/api"
import type { ChunkItem } from "@/types"

export default function ExportPage() {
  const router = useRouter()
  const [chunks, setChunks] = useState<ChunkItem[]>([])
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  const stored = typeof window !== "undefined" ? localStorage.getItem("project_id") : null

  useEffect(() => {
    let cancelled = false
    if (!stored) {
      router.replace("/")
      return
    }
    const pid = Number(stored)
    const load = async () => {
      try {
        const data = await listChunks(pid)
        if (!cancelled) setChunks(data)
      } catch {
        // ignore
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [router, stored])

  const handleDownload = useCallback(async (format: "csv" | "json") => {
    const pid = stored ? Number(stored) : null
    if (!pid) return
    try {
      const data = await fetchExportData(pid, format)
      const text = typeof data === "string" ? data : JSON.stringify(data, null, 2)
      const blob = new Blob([text], {
        type: format === "json" ? "application/json" : "text/csv",
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `localized_script_${pid}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      // ignore
    }
  }, [stored])

  const handleCopyJson = useCallback(async () => {
    const pid = stored ? Number(stored) : null
    if (!pid) return
    try {
      const data = await fetchExportData(pid, "json")
      const text = typeof data === "string" ? data : JSON.stringify(data, null, 2)
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // ignore
    }
  }, [stored])

  if (loading) {
    return <StateMessage>Loading...</StateMessage>
  }

  const projectId = stored ? Number(stored) : null
  const total = chunks.length
  const translated = chunks.filter((c) => c.status === "translated").length

  if (!projectId || total === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="mb-2 text-3xl font-bold text-zinc-900">Export</h1>
        <p className="mb-8 text-zinc-500">
          Download your localized script or copy it to clipboard.
        </p>
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-10 text-center text-sm text-zinc-400">
          No project found. Start by uploading files on the Upload page.
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-2 text-3xl font-bold text-zinc-900">Export</h1>
      <p className="mb-8 text-zinc-500">
        Download your localized script or copy it to clipboard.
      </p>

      <div className="mb-8 rounded-xl border border-zinc-200 bg-white p-6">
        <h2 className="mb-3 text-lg font-semibold text-zinc-800">
          Project #{projectId}
        </h2>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="rounded-lg bg-zinc-50 p-3">
            <div className="text-2xl font-bold text-zinc-800">{total}</div>
            <div className="text-xs text-zinc-500">Total Chunks</div>
          </div>
          <div className="rounded-lg bg-green-50 p-3">
            <div className="text-2xl font-bold text-green-700">
              {translated}
            </div>
            <div className="text-xs text-green-600">Translated</div>
          </div>
          <div className="rounded-lg bg-zinc-50 p-3">
            <div className="text-2xl font-bold text-zinc-800">
              {total - translated}
            </div>
            <div className="text-xs text-zinc-500">Pending</div>
          </div>
        </div>
      </div>

      {translated === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-10 text-center text-sm text-zinc-400">
          No localized lines available for export yet.
        </div>
      ) : (
        <div className="flex flex-wrap gap-4">
          <button
            type="button"
            onClick={() => handleDownload("csv")}
            className="inline-flex items-center gap-2 rounded-xl bg-zinc-900 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-zinc-700"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Download CSV
          </button>
          <button
            type="button"
            onClick={() => handleDownload("json")}
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-300 bg-white px-6 py-3 text-sm font-semibold text-zinc-700 transition-colors hover:bg-zinc-50"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Download JSON
          </button>
          <button
            type="button"
            onClick={handleCopyJson}
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-300 bg-white px-6 py-3 text-sm font-semibold text-zinc-700 transition-colors hover:bg-zinc-50"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
              />
            </svg>
            {copied ? "Copied!" : "Copy JSON"}
          </button>
        </div>
      )}
    </div>
  )
}

function StateMessage({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-24 text-center text-zinc-500">
      {children}
    </div>
  )
}
