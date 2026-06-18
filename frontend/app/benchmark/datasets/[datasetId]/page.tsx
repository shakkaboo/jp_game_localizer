"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { getDataset, startRun } from "@/lib/benchmark-api"
import type { BenchmarkDatasetRead } from "@/types/benchmark"
import StatusBadge from "@/components/benchmark/StatusBadge"
import { LoadingState, ErrorState } from "@/components/benchmark/LoadingState"

type RunningState = "idle" | "confirming" | "running" | "done"

export default function DatasetDetailPage() {
  const params = useParams<{ datasetId: string }>()
  const router = useRouter()
  const datasetId = Number(params.datasetId)

  const [dataset, setDataset] = useState<BenchmarkDatasetRead | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [runningMode, setRunningMode] = useState<RunningState>("idle")
  const [selectedMode, setSelectedMode] = useState<string | null>(null)
  const [runError, setRunError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getDataset(datasetId)
      setDataset(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dataset")
    } finally {
      setLoading(false)
    }
  }, [datasetId])

  useEffect(() => {
    let cancelled = false
    const loadData = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await getDataset(datasetId)
        if (!cancelled) setDataset(data)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load dataset")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadData()
    return () => { cancelled = true }
  }, [datasetId])

  const handleStartRun = async () => {
    if (!selectedMode || runningMode === "running") return
    setRunningMode("running")
    setRunError(null)
    try {
      const result = await startRun(datasetId, selectedMode)
      router.push(`/benchmark/runs/${result.run_id}`)
    } catch (e) {
      setRunError(e instanceof Error ? e.message : "Failed to start run")
      setRunningMode("idle")
    }
  }

  if (loading) return <LoadingState message="Loading dataset..." />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!dataset) return <LoadingState message="Dataset not found." />

  return (
    <div className="mx-auto max-w-4xl px-4 py-12">
      <button
        type="button"
        onClick={() => router.push("/benchmark")}
        className="mb-4 text-sm text-zinc-400 hover:text-zinc-600"
      >
        &larr; Back to Benchmark
      </button>

      <div className="mb-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-zinc-900">{dataset.name}</h1>
            <p className="mt-1 text-zinc-500">
              v{dataset.version} &middot; {dataset.source_or_author}
            </p>
          </div>
          <StatusBadge status={dataset.review_status} />
        </div>

        {dataset.description && (
          <p className="mt-4 text-sm text-zinc-600">{dataset.description}</p>
        )}

        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat label="License" value={dataset.license_or_usage_status} />
          <Stat
            label="Reference Method"
            value={dataset.reference_translation_method}
          />
          <Stat label="Scenes" value={String(dataset.scenes.length)} />
          <Stat
            label="Items"
            value={String(dataset.scenes.reduce((s, sc) => s + sc.items.length, 0))}
          />
        </div>
      </div>

      <div className="mb-8 rounded-xl border border-zinc-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-zinc-800">
          Start a Benchmark Run
        </h2>
        <p className="mb-4 text-sm text-zinc-500">
          Select a mode and start a run. This will make live LLM calls for all{" "}
          {dataset.scenes.reduce((s, sc) => s + sc.items.length, 0)} items across{" "}
          {dataset.scenes.length} scenes.
        </p>

        {runError && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {runError}
          </div>
        )}

        <div className="flex flex-wrap gap-3">
          {(["plain", "context", "context_memory"] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => {
                setSelectedMode(mode)
                setRunningMode("confirming")
                setRunError(null)
              }}
              disabled={runningMode === "running"}
              className="rounded-lg border border-zinc-300 bg-white px-5 py-2.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:opacity-50"
            >
              Run {mode === "context_memory" ? "Context + Memory" : mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>

        {runningMode === "confirming" && selectedMode && (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="mb-3 text-sm font-medium text-amber-800">
              Start a <strong>{selectedMode.replace("_", " + ")}</strong> run? This
              will call the LLM for each item in the dataset and may take some time.
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleStartRun}
                className="rounded-lg bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
              >
                Confirm &amp; Start
              </button>
              <button
                type="button"
                onClick={() => setRunningMode("idle")}
                className="rounded-lg border border-zinc-300 bg-white px-5 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {runningMode === "running" && (
          <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
            Running benchmark across {dataset.scenes.length} scenes. Keep this page
            open.
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-zinc-800">Scenes</h2>
        <div className="space-y-3">
          {dataset.scenes.map((scene) => (
            <div
              key={scene.id}
              className="rounded-xl border border-zinc-200 bg-white p-5"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-base font-semibold text-zinc-800">
                    {scene.scene_number}. {scene.title || `Scene ${scene.scene_number}`}
                  </h3>
                  <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
                    <span>{scene.genre}</span>
                    <span>{scene.content_type}</span>
                    {scene.setting_or_location && <span>{scene.setting_or_location}</span>}
                    {scene.tone && <span>Tone: {scene.tone}</span>}
                    <span>{scene.items.length} items</span>
                  </div>
                </div>
              </div>
              {scene.notes && (
                <p className="mt-2 text-xs text-zinc-400">{scene.notes}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="mt-0.5 text-sm font-medium text-zinc-800">{value}</p>
    </div>
  )
}
