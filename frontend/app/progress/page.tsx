"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import ProgressCard from "@/components/ProgressCard"
import { listChunks, translateChunk } from "@/lib/api"
import type { ChunkItem } from "@/types"

export default function ProgressPage() {
  const router = useRouter()
  const [chunks, setChunks] = useState<ChunkItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [translatingId, setTranslatingId] = useState<number | null>(null)
  const [projectId, setProjectId] = useState<number | null>(null)

  const loadChunks = useCallback(async (pid: number) => {
    try {
      const data = await listChunks(pid)
      setChunks(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load chunks")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const stored = localStorage.getItem("project_id")
    if (!stored) {
      router.replace("/")
      return
    }
    const pid = Number(stored)
    setProjectId(pid)
    loadChunks(pid)
  }, [router, loadChunks])

  const handleTranslate = async (chunkId: number) => {
    setTranslatingId(chunkId)
    try {
      await translateChunk(chunkId)
      if (projectId) await loadChunks(projectId)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Translation failed")
    } finally {
      setTranslatingId(null)
    }
  }

  const handleReview = (chunkId: number) => {
    router.push(`/review/${chunkId}`)
  }

  if (loading) {
    return <StateMessage>Loading chunks...</StateMessage>
  }

  if (error) {
    return (
      <StateMessage>
        <p className="text-red-600">{error}</p>
        <button
          type="button"
          onClick={() => projectId && loadChunks(projectId)}
          className="mt-3 rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white"
        >
          Retry
        </button>
      </StateMessage>
    )
  }

  const total = chunks.length
  const translated = chunks.filter((c) => c.status === "translated").length
  const pending = total - translated
  const pct = total > 0 ? Math.round((translated / total) * 100) : 0

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-2 text-3xl font-bold text-zinc-900">
        Localization Progress
      </h1>
      <p className="mb-8 text-zinc-500">
        Project #{projectId} &middot; {total} chunk{total !== 1 ? "s" : ""}
      </p>

      <div className="mb-8 rounded-xl border border-zinc-200 bg-white p-6">
        <div className="mb-3 flex items-center justify-between text-sm">
          <span className="font-medium text-zinc-700">
            {translated} translated
          </span>
          <span className="text-zinc-400">
            {pending} pending &middot; {pct}%
          </span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-zinc-100">
          <div
            className="h-full rounded-full bg-green-500 transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="mt-3 flex gap-4 text-xs text-zinc-400">
          <span>
            <span className="inline-block h-2 w-2 rounded-full bg-green-500" />{" "}
            Translated
          </span>
          <span>
            <span className="inline-block h-2 w-2 rounded-full bg-zinc-200" />{" "}
            Pending
          </span>
        </div>
      </div>

      {chunks.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-10 text-center text-sm text-zinc-400">
          No chunks found for this project. Go back and create chunks first.
        </div>
      ) : (
        <div className="space-y-3">
          {chunks.map((chunk) => (
            <ProgressCard
              key={chunk.id}
              chunk={chunk}
              onTranslate={handleTranslate}
              onReview={handleReview}
              translating={translatingId === chunk.id}
            />
          ))}
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
