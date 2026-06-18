"use client"

import type { BenchmarkHumanMetricsSummary } from "@/types/benchmark"
import { formatNullableMetric } from "@/lib/benchmark-helpers"

interface Props {
  humanMetrics: BenchmarkHumanMetricsSummary | null
  label: string
}

export default function HumanItemMetricsComparison({ humanMetrics, label }: Props) {
  if (!humanMetrics) {
    return (
      <div className="space-y-2 text-xs">
        <p className="font-semibold text-zinc-800">{label}</p>
        <p className="text-zinc-400 italic">No human item-review data</p>
      </div>
    )
  }

  const { item_scores } = humanMetrics

  return (
    <div className="space-y-2 text-xs">
      <p className="font-semibold text-zinc-800">{label}</p>
      <Row k="Item Review Coverage" v={`${(humanMetrics.item_review_coverage_percentage * 100).toFixed(1)}%`} />
      <Row k="Evaluations" v={String(item_scores.item_evaluation_count)} />
      <Row k="Unique Outputs Reviewed" v={String(item_scores.unique_reviewed_output_count)} />
      <Row k="Reviewers per Output" v={formatNullableMetric(item_scores.average_reviewers_per_reviewed_output)} />
      <Row k="Average Total" v={formatNullableMetric(item_scores.average_total) + " / 100"} />

      {Object.keys(item_scores.average_per_criterion).length > 0 && (
        <details className="mt-1">
          <summary className="cursor-pointer text-xs font-medium text-zinc-500 hover:text-zinc-700">
            Criterion means
          </summary>
          <div className="mt-1 space-y-1 pl-2">
            {Object.entries(item_scores.average_per_criterion).map(([key, stats]) => (
              <div key={key} className="flex justify-between">
                <span className="text-zinc-500">{key}</span>
                <span className="text-zinc-700">{formatNullableMetric(stats?.mean ?? null)}</span>
              </div>
            ))}
          </div>
        </details>
      )}

      {item_scores.requires_previous_memory && (
        <Row k="Memory-dep avg" v={formatNullableMetric((item_scores.requires_previous_memory as Record<string, number>)?.average_total ?? null)} />
      )}
      {item_scores.no_previous_memory && (
        <Row k="No-memory avg" v={formatNullableMetric((item_scores.no_previous_memory as Record<string, number>)?.average_total ?? null)} />
      )}
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
