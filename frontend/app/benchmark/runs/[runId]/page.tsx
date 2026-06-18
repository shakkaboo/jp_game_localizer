"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { getRun, getRunMetrics, getHumanMetrics } from "@/lib/benchmark-api"
import type { BenchmarkRunDetailRead, BenchmarkMetricsSummary, BenchmarkHumanMetricsSummary } from "@/types/benchmark"
import ModeBadge from "@/components/benchmark/ModeBadge"
import StatusBadge from "@/components/benchmark/StatusBadge"
import WarningBanner from "@/components/benchmark/WarningBanner"
import ScenePanel from "@/components/benchmark/ScenePanel"
import MetricsSummary from "@/components/benchmark/MetricsSummary"
import { LoadingState, ErrorState } from "@/components/benchmark/LoadingState"

export default function RunDetailPage() {
  const params = useParams<{ runId: string }>()
  const router = useRouter()
  const runId = Number(params.runId)

  const [run, setRun] = useState<BenchmarkRunDetailRead | null>(null)
  const [metrics, setMetrics] = useState<BenchmarkMetricsSummary | null>(null)
  const [humanMetrics, setHumanMetrics] = useState<BenchmarkHumanMetricsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAllScenes, setShowAllScenes] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [runData, metricsData, hmData] = await Promise.all([
        getRun(runId),
        getRunMetrics(runId),
        getHumanMetrics(runId).catch(() => null),
      ])
      setRun(runData)
      setMetrics(metricsData)
      setHumanMetrics(hmData)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load run")
    } finally {
      setLoading(false)
    }
  }, [runId])

  useEffect(() => {
    let cancelled = false
    const loadData = async () => {
      setLoading(true)
      setError(null)
      try {
        const [runData, metricsData, hmData] = await Promise.all([
          getRun(runId),
          getRunMetrics(runId),
          getHumanMetrics(runId).catch(() => null),
        ])
        if (!cancelled) {
          setRun(runData)
          setMetrics(metricsData)
          setHumanMetrics(hmData)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load run")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadData()
    return () => { cancelled = true }
  }, [runId])

  if (loading) return <LoadingState message="Loading run results..." />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!run) return <LoadingState message="Run not found." />

  const isPending = run.status === "pending" || run.status === "running"

  return (
    <div className="mx-auto max-w-5xl px-4 py-12">
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
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-zinc-900">
                Run #{run.id}
              </h1>
              <ModeBadge mode={run.mode} />
              <StatusBadge status={run.status} />
            </div>
            <p className="mt-1 text-sm text-zinc-500">{run.dataset_id}</p>
          </div>
          <button
            type="button"
            onClick={() => router.push(`/benchmark/runs/${runId}/review`)}
            className="rounded-lg bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
          >
            Review this run
          </button>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat label="Provider" value={run.llm_provider} />
          <Stat label="Model" value={run.llm_model} />
          <Stat label="Prompt Version" value={run.prompt_version} />
          <Stat
            label="Progress"
            value={`${run.completed_scenes}/${run.total_scenes} scenes`}
          />
          <Stat
            label="Created"
            value={new Date(run.created_at).toLocaleString()}
          />
          <Stat
            label="Completed"
            value={
              run.completed_at
                ? new Date(run.completed_at).toLocaleString()
                : "—"
            }
          />
        </div>

        {isPending && (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800">
            This run is {run.status}. Results will appear when complete.
          </div>
        )}

        {run.memory_gap && (
          <div className="mt-4">
            <WarningBanner
              message="Memory gap detected — some scenes required previous memory but no prior scene output was available."
              type="warning"
            />
          </div>
        )}

        {run.error_message && (
          <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
            {run.error_message}
          </div>
        )}

        {humanMetrics && (
          <div className="mt-6 grid grid-cols-3 gap-3">
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
              <p className="text-xs text-zinc-500">Item Review Coverage</p>
              <p className="mt-0.5 text-sm font-semibold text-zinc-800">
                {(humanMetrics.item_review_coverage_percentage * 100).toFixed(1)}%
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
              <p className="text-xs text-zinc-500">Scene Review Coverage</p>
              <p className="mt-0.5 text-sm font-semibold text-zinc-800">
                {(humanMetrics.scene_review_coverage_percentage * 100).toFixed(1)}%
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
              <p className="text-xs text-zinc-500">Hard-Failure Review Coverage</p>
              <p className="mt-0.5 text-sm font-semibold text-zinc-800">
                {(humanMetrics.hard_failure_review_coverage_percentage * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        )}
      </div>

      {metrics && !isPending && (
        <div className="mb-8">
          <h2 className="mb-4 text-xl font-semibold text-zinc-800">
            Automatic Metrics
          </h2>
          <MetricsSummary metrics={metrics} />
        </div>
      )}

      {run.scenes.length > 0 && (
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-zinc-800">
              Scene Outputs ({run.scenes.length})
            </h2>
            <button
              type="button"
              onClick={() => setShowAllScenes(!showAllScenes)}
              className="text-sm text-zinc-500 hover:text-zinc-700"
            >
              {showAllScenes ? "Collapse all" : "Expand all"}
            </button>
          </div>
          <div className="space-y-3">
            {run.scenes.map((so) => (
              <ScenePanel
                key={so.scene.id}
                sceneOutput={so}
                defaultOpen={showAllScenes}
              />
            ))}
          </div>
        </div>
      )}

      {run.scenes.length === 0 && !isPending && (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-10 text-center text-sm text-zinc-400">
          No scene outputs for this run.
        </div>
      )}
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
