"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import ReviewTable from "@/components/ReviewTable"
import StatusBadge from "@/components/StatusBadge"
import { getChunkDetail, translateChunk, patchTranslation } from "@/lib/api"
import type { ChunkDetail } from "@/types"

export default function ReviewPage() {
  const params = useParams<{ chunkId: string }>()
  const router = useRouter()
  const chunkId = Number(params.chunkId)

  const [detail, setDetail] = useState<ChunkDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [translating, setTranslating] = useState(false)
  const [saving, setSaving] = useState<number | null>(null)
  const [memoryOpen, setMemoryOpen] = useState(false)

  const loadDetail = useCallback(async () => {
    try {
      const data = await getChunkDetail(chunkId)
      setDetail(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load")
    } finally {
      setLoading(false)
    }
  }, [chunkId])

  useEffect(() => {
    loadDetail()
  }, [loadDetail])

  const handleTranslate = async () => {
    setTranslating(true)
    setError(null)
    try {
      await translateChunk(chunkId)
      await loadDetail()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Translation failed")
    } finally {
      setTranslating(false)
    }
  }

  const handleSave = async (
    translationId: number,
    field: string,
    value: string
  ) => {
    setSaving(translationId)
    try {
      await patchTranslation(translationId, { [field]: value })
    } catch {
      setError("Failed to save")
    } finally {
      setSaving(null)
    }
  }

  if (loading) {
    return <StateMessage>Loading chunk...</StateMessage>
  }

  if (error && !detail) {
    return (
      <StateMessage>
        <p className="text-red-600">{error}</p>
        <button
          type="button"
          onClick={loadDetail}
          className="mt-3 rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white"
        >
          Retry
        </button>
      </StateMessage>
    )
  }

  if (!detail) {
    return <StateMessage>Chunk not found.</StateMessage>
  }

  const hasMemory = detail.previous_memory_json || detail.chunk_memory_json
  const isTranslated = detail.status === "translated"

  return (
    <div className="mx-auto max-w-4xl px-4 py-12">
      <div className="mb-8">
        <button
          type="button"
          onClick={() => router.push("/progress")}
          className="mb-4 text-sm text-zinc-400 hover:text-zinc-600"
        >
          &larr; Back to Progress
        </button>

        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-zinc-900">
            {detail.chunk_title}
          </h1>
          <StatusBadge status={detail.status} />
        </div>
        {detail.scene_hint && (
          <p className="mt-1 text-sm text-zinc-500">
            Scene: {detail.scene_hint} &middot; Chunk #{detail.chunk_number}
          </p>
        )}
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {hasMemory && (
        <div className="mb-8 rounded-xl border border-zinc-200">
          <button
            type="button"
            onClick={() => setMemoryOpen(!memoryOpen)}
            className="flex w-full items-center justify-between px-5 py-3 text-left text-sm font-medium text-zinc-600 hover:bg-zinc-50"
          >
            Story Memory
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className={`h-4 w-4 transition-transform ${
                memoryOpen ? "rotate-180" : ""
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
          {memoryOpen && (
            <div className="border-t border-zinc-200 px-5 py-4">
              {detail.previous_memory_json && (
                <div className="mb-3">
                  <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                    Previous Memory
                  </h4>
                  <pre className="max-h-48 overflow-auto rounded-md bg-zinc-50 p-3 text-xs text-zinc-600">
                    {JSON.stringify(
                      JSON.parse(detail.previous_memory_json),
                      null,
                      2
                    )}
                  </pre>
                </div>
              )}
              {detail.chunk_memory_json && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                    Chunk Memory
                  </h4>
                  <pre className="max-h-48 overflow-auto rounded-md bg-zinc-50 p-3 text-xs text-zinc-600">
                    {JSON.stringify(
                      JSON.parse(detail.chunk_memory_json),
                      null,
                      2
                    )}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!isTranslated && (
        <div className="mb-8 flex items-center gap-4 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
          <p className="flex-1 text-sm text-amber-800">
            This chunk has not been translated yet.
          </p>
          <button
            type="button"
            onClick={handleTranslate}
            disabled={translating}
            className="rounded-lg bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50"
          >
            {translating ? "Translating..." : "Translate this Chunk"}
          </button>
        </div>
      )}

      <ReviewTable
        sourceLines={detail.source_lines}
        translations={detail.translations}
        onSave={handleSave}
        saving={saving}
      />

      {detail.source_lines.length === 0 && (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-10 text-center text-sm text-zinc-400">
          No source lines in this chunk.
        </div>
      )}
    </div>
  )
}

function StateMessage({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-4xl px-4 py-24 text-center text-zinc-500">
      {children}
    </div>
  )
}
