"use client"

import type { BenchmarkHumanMetricsSummary } from "@/types/benchmark"
import { formatCoveragePercentage, formatHardFailureRatePercentage } from "@/lib/benchmark-helpers"

interface Props {
  humanMetrics: BenchmarkHumanMetricsSummary | null
  label: string
}

export default function HardFailureMetricsComparison({ humanMetrics, label }: Props) {
  if (!humanMetrics) {
    return (
      <div className="space-y-2 text-xs">
        <p className="font-semibold text-zinc-800">{label}</p>
        <p className="text-zinc-400 italic">No human item-review data</p>
      </div>
    )
  }

  const { hard_failures, hard_failure_review_coverage_percentage } = humanMetrics

  return (
    <div className="space-y-2 text-xs">
      <p className="font-semibold text-zinc-800">{label}</p>
      <Row k="HF Review Coverage" v={formatCoveragePercentage(hard_failure_review_coverage_percentage)} />
      <Row k="Reviews" v={String(hard_failures.hard_failure_review_count)} />
      <Row k="Unique Outputs Reviewed" v={String(hard_failures.unique_outputs_reviewed_for_hard_failures)} />
      <Row k="Outputs with Any HF" v={String(hard_failures.outputs_with_any_hard_failure)} />
      <Row
        k="HF Rate"
        v={formatHardFailureRatePercentage(hard_failures.hard_failure_rate_among_reviewed_outputs, 1)}
      />

      {Object.keys(hard_failures.count_per_flag).length > 0 && (
        <details className="mt-1">
          <summary className="cursor-pointer text-xs font-medium text-zinc-500 hover:text-zinc-700">
            Count per flag
          </summary>
          <div className="mt-1 space-y-1 pl-2">
            {Object.entries(hard_failures.count_per_flag).map(([key, count]) => (
              <div key={key} className="flex justify-between">
                <span className="text-zinc-500">{key.replace(/_/g, " ")}</span>
                <span className="text-zinc-700">{count}</span>
              </div>
            ))}
          </div>
        </details>
      )}

      <p className="mt-1 italic text-zinc-400">
        Rate among outputs that received a hard-failure review.
      </p>
    </div>
  )
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-zinc-500">{k}</span>
      <span className="font-medium text-zinc-800">{v}</span>
    </div>
  )
}
