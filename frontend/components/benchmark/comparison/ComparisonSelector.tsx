"use client"

import { useMemo } from "react"
import type { BenchmarkRunRead } from "@/types/benchmark"

interface Props {
  datasets: { id: number; name: string; version: string }[]
  runs: BenchmarkRunRead[]
  mode: "explicit" | "latest"
  onModeChange: (mode: "explicit" | "latest") => void
  selectedDatasetId: number | null
  onDatasetChange: (id: number | null) => void
  plainRunId: number | null
  contextRunId: number | null
  contextMemoryRunId: number | null
  onPlainRunChange: (id: number | null) => void
  onContextRunChange: (id: number | null) => void
  onContextMemoryRunChange: (id: number | null) => void
  onCompare: () => void
  loading: boolean
}

export default function ComparisonSelector({
  datasets,
  runs,
  mode,
  onModeChange,
  selectedDatasetId,
  onDatasetChange,
  plainRunId,
  contextRunId,
  contextMemoryRunId,
  onPlainRunChange,
  onContextRunChange,
  onContextMemoryRunChange,
  onCompare,
  loading,
}: Props) {
  const completedRuns = useMemo(
    () => runs.filter((r) => r.status === "completed" || r.status === "completed_with_errors"),
    [runs]
  )

  const filteredRuns = useMemo(
    () => (selectedDatasetId ? completedRuns.filter((r) => r.dataset_id === selectedDatasetId) : completedRuns),
    [completedRuns, selectedDatasetId]
  )

  const validForCompare = useMemo(() => {
    if (mode === "explicit") {
      return (
        plainRunId !== null &&
        contextRunId !== null &&
        contextMemoryRunId !== null &&
        new Set([plainRunId, contextRunId, contextMemoryRunId]).size === 3
      )
    }
    return selectedDatasetId !== null
  }, [mode, plainRunId, contextRunId, contextMemoryRunId, selectedDatasetId])

  return (
    <div className="space-y-4 rounded-xl border border-zinc-200 bg-white p-5">
      {/* Mode selector */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onModeChange("explicit")}
          className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
            mode === "explicit"
              ? "border-zinc-800 bg-zinc-800 text-white"
              : "border-zinc-300 bg-white text-zinc-600 hover:bg-zinc-50"
          }`}
        >
          Select Explicit Runs
        </button>
        <button
          type="button"
          onClick={() => onModeChange("latest")}
          className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
            mode === "latest"
              ? "border-zinc-800 bg-zinc-800 text-white"
              : "border-zinc-300 bg-white text-zinc-600 hover:bg-zinc-50"
          }`}
        >
          Latest Completed per Mode
        </button>
      </div>

      {/* Dataset selector */}
      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700">
          Dataset
        </label>
        <select
          value={selectedDatasetId ?? ""}
          onChange={(e) => {
            const val = e.target.value
            onDatasetChange(val ? Number(val) : null)
          }}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-800"
        >
          <option value="">Select a dataset...</option>
          {datasets.map((ds) => (
            <option key={ds.id} value={ds.id}>
              {ds.name} v{ds.version}
            </option>
          ))}
        </select>
      </div>

      {mode === "explicit" && (
        <div className="grid gap-3 sm:grid-cols-3">
          <RunSelect
            label="Plain"
            selectId="run-plain"
            runs={filteredRuns.filter((r) => r.mode === "plain")}
            value={plainRunId}
            onChange={onPlainRunChange}
            excludeIds={contextRunId && contextMemoryRunId ? [contextRunId, contextMemoryRunId] : []}
          />
          <RunSelect
            label="Context"
            selectId="run-context"
            runs={filteredRuns.filter((r) => r.mode === "context")}
            value={contextRunId}
            onChange={onContextRunChange}
            excludeIds={plainRunId && contextMemoryRunId ? [plainRunId, contextMemoryRunId] : []}
          />
          <RunSelect
            label="Context + Memory"
            selectId="run-context-memory"
            runs={filteredRuns.filter((r) => r.mode === "context_memory")}
            value={contextMemoryRunId}
            onChange={onContextMemoryRunChange}
            excludeIds={plainRunId && contextRunId ? [plainRunId, contextRunId] : []}
          />
        </div>
      )}

      {mode === "latest" && (
        <p className="text-xs text-zinc-500">
          The backend selects the latest completed/complete-with-errors run for each mode.
        </p>
      )}

      <button
        type="button"
        onClick={onCompare}
        disabled={!validForCompare || loading}
        className="rounded-lg bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-40"
      >
        {loading ? "Loading..." : "Compare Modes"}
      </button>
    </div>
  )
}

function RunSelect({
  label,
  selectId,
  runs,
  value,
  onChange,
  excludeIds,
}: {
  label: string
  selectId: string
  runs: BenchmarkRunRead[]
  value: number | null
  onChange: (id: number | null) => void
  excludeIds: number[]
}) {
  const available = runs.filter((r) => !excludeIds.includes(r.id))

  return (
    <div>
      <label htmlFor={selectId} className="mb-1 block text-sm font-medium text-zinc-700">{label}</label>
      <select
        id={selectId}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
        className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-800"
      >
        <option value="">Select {label} run...</option>
        {available.map((r) => (
          <option key={r.id} value={r.id}>
            Run #{r.id} — {r.llm_model} ({r.status})
          </option>
        ))}
        {available.length === 0 && (
          <option value="" disabled>
            No {label} runs available
          </option>
        )}
      </select>
    </div>
  )
}
