"use client"

import { useEffect, useState } from "react"
import { listDatasets, listRuns } from "@/lib/benchmark-api"
import type { BenchmarkDatasetListItem, BenchmarkRunRead } from "@/types/benchmark"
import DatasetCard from "@/components/benchmark/DatasetCard"
import { LoadingState, EmptyState, ErrorState } from "@/components/benchmark/LoadingState"

export default function BenchmarkPage() {
  const [datasets, setDatasets] = useState<BenchmarkDatasetListItem[]>([])
  const [runs, setRuns] = useState<BenchmarkRunRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [ds, allRuns] = await Promise.all([listDatasets(), listRuns()])
      setDatasets(ds)
      setRuns(allRuns)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load benchmark data")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    const loadData = async () => {
      setLoading(true)
      setError(null)
      try {
        const [ds, allRuns] = await Promise.all([listDatasets(), listRuns()])
        if (!cancelled) {
          setDatasets(ds)
          setRuns(allRuns)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load benchmark data")
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadData()
    return () => { cancelled = true }
  }, [])

  if (loading) return <LoadingState message="Loading benchmark datasets..." />
  if (error) return <ErrorState message={error} onRetry={load} />

  return (
    <div className="mx-auto max-w-5xl px-4 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-zinc-900">Benchmark</h1>
        <p className="mt-1 text-zinc-500">
          Scene-aware evaluation of JP→EN game localization across three modes.
        </p>
        <a
          href="/benchmark/compare"
          className="mt-3 inline-block rounded-lg bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
        >
          Compare Modes
        </a>
      </div>

      {datasets.length === 0 ? (
        <EmptyState message="No benchmark datasets loaded yet. Use the backend API to load a dataset first." />
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {datasets.map((ds) => (
            <DatasetCard
              key={ds.id}
              dataset={ds}
              latestRuns={runs.filter((r) => r.dataset_id === ds.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
