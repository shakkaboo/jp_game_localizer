"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { listDatasets, listRuns, compareExplicitRuns, compareLatestCompleted } from "@/lib/benchmark-api"
import type { BenchmarkDatasetListItem, BenchmarkRunRead, BenchmarkComparisonReport } from "@/types/benchmark"
import { LoadingState, EmptyState, ErrorState } from "@/components/benchmark/LoadingState"
import ComparisonSelector from "@/components/benchmark/comparison/ComparisonSelector"
import ComparisonTable from "@/components/benchmark/comparison/ComparisonTable"
import ComparisonWarnings from "@/components/benchmark/comparison/ComparisonWarnings"
import ComparisonNote from "@/components/benchmark/comparison/ComparisonNote"

export default function ComparePage() {
  const router = useRouter()

  const [datasets, setDatasets] = useState<BenchmarkDatasetListItem[]>([])
  const [runs, setRuns] = useState<BenchmarkRunRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [compareLoading, setCompareLoading] = useState(false)
  const [compareError, setCompareError] = useState<string | null>(null)
  const [report, setReport] = useState<BenchmarkComparisonReport | null>(null)

  const [mode, setMode] = useState<"explicit" | "latest">("explicit")
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null)
  const [plainRunId, setPlainRunId] = useState<number | null>(null)
  const [contextRunId, setContextRunId] = useState<number | null>(null)
  const [contextMemoryRunId, setContextMemoryRunId] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [ds, r] = await Promise.all([listDatasets(), listRuns()])
        if (!cancelled) {
          setDatasets(ds)
          setRuns(r)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load data")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const handleCompare = useCallback(async () => {
    setCompareLoading(true)
    setCompareError(null)
    setReport(null)
    try {
      let result: BenchmarkComparisonReport
      if (mode === "explicit" && plainRunId && contextRunId && contextMemoryRunId) {
        result = await compareExplicitRuns(plainRunId, contextRunId, contextMemoryRunId)
      } else if (mode === "latest" && selectedDatasetId) {
        result = await compareLatestCompleted(selectedDatasetId)
      } else {
        throw new Error("Invalid comparison parameters")
      }
      setReport(result)
    } catch (e) {
      setCompareError(e instanceof Error ? e.message : "Comparison failed")
    } finally {
      setCompareLoading(false)
    }
  }, [mode, plainRunId, contextRunId, contextMemoryRunId, selectedDatasetId])

  const handleModeChange = useCallback((newMode: "explicit" | "latest") => {
    setMode(newMode)
    setReport(null)
    setCompareError(null)
    if (newMode === "latest") {
      setPlainRunId(null)
      setContextRunId(null)
      setContextMemoryRunId(null)
    }
  }, [])

  const handleDatasetChange = useCallback((id: number | null) => {
    setSelectedDatasetId(id)
    setReport(null)
    setCompareError(null)
    setPlainRunId(null)
    setContextRunId(null)
    setContextMemoryRunId(null)
  }, [])

  if (loading) return <LoadingState message="Loading comparison data..." />
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />

  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <button
        type="button"
        onClick={() => router.push("/benchmark")}
        className="mb-4 text-sm text-zinc-400 hover:text-zinc-600"
      >
        &larr; Back to Benchmark
      </button>

      <div className="mb-6">
        <h1 className="text-3xl font-bold text-zinc-900">Compare Modes</h1>
        <p className="mt-1 text-zinc-500">
          Three-mode comparison of plain, context, and context+memory runs.
        </p>
      </div>

      {datasets.length === 0 ? (
        <EmptyState message="No datasets available. Load a dataset first." />
      ) : (
        <>
          <div className="mb-8">
            <ComparisonSelector
              datasets={datasets}
              runs={runs}
              mode={mode}
              onModeChange={handleModeChange}
              selectedDatasetId={selectedDatasetId}
              onDatasetChange={handleDatasetChange}
              plainRunId={plainRunId}
              contextRunId={contextRunId}
              contextMemoryRunId={contextMemoryRunId}
              onPlainRunChange={setPlainRunId}
              onContextRunChange={setContextRunId}
              onContextMemoryRunChange={setContextMemoryRunId}
              onCompare={handleCompare}
              loading={compareLoading}
            />
          </div>

          {compareError && (
            <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
              {compareError}
            </div>
          )}

          {report && (
            <div className="space-y-6">
              <div className="rounded-xl border border-zinc-200 bg-white px-5 py-4">
                <h2 className="text-lg font-semibold text-zinc-800">
                  {report.dataset_name} v{report.dataset_version}
                </h2>
              </div>

              <ComparisonWarnings warnings={report.warnings} />
              <ComparisonTable entries={report.runs} />
              <ComparisonNote note={report.note} />

              {report.runs.length < 3 && (
                <div className="rounded-xl border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm text-zinc-500">
                  Only {report.runs.length} of 3 modes have completed runs available.
                  {report.runs.length === 0 && " No completed runs found for this dataset."}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
