"use client"

import type { BenchmarkHumanMetricsSummary } from "@/types/benchmark"
import { formatCoveragePercentage, formatHardFailureRatePercentage, formatNullableMetric } from "@/lib/benchmark-helpers"
import ReviewCoverageCard from "./ReviewCoverageCard"

interface Props {
  metrics: BenchmarkHumanMetricsSummary
}

function CriterionRow({ name, stats }: { name: string; stats: { mean: number | null; std: number | null } | null }) {
  return (
    <tr className="border-b border-zinc-100 text-xs">
      <td className="py-1.5 pr-4 text-zinc-700">{name}</td>
      <td className="py-1.5 pr-4 text-right text-zinc-600">{formatNullableMetric(stats?.mean ?? null)}</td>
      <td className="py-1.5 text-right text-zinc-400">{formatNullableMetric(stats?.std ?? null)}</td>
    </tr>
  )
}

function ReviewerRow({ name, value }: { name: string; value: unknown }) {
  const avg = typeof value === "object" && value !== null
    ? formatNullableMetric((value as Record<string, number>).average_total ?? null)
    : typeof value === "number" ? formatNullableMetric(value) : "—"
  return (
    <tr className="border-b border-zinc-100 text-xs">
      <td className="py-1.5 pr-4 text-zinc-700">{name}</td>
      <td className="py-1.5 text-right text-zinc-600">{avg}</td>
    </tr>
  )
}

function BreakdownTable({ data, title }: { data: Record<string, unknown> | null; title: string }) {
  if (!data || Object.keys(data).length === 0) return null
  return (
    <div className="mt-3">
      <p className="mb-1 text-xs font-medium text-zinc-500">{title}</p>
      <table className="w-full">
        <tbody>
          {Object.entries(data).map(([key, val]) => {
            if (val === null) return null
            return <ReviewerRow key={key} name={key} value={val} />
          })}
        </tbody>
      </table>
    </div>
  )
}

export default function HumanMetricsPanel({ metrics }: Props) {
  const { item_scores, scene_scores, hard_failures } = metrics

  return (
    <div className="space-y-8">
      {/* Coverage */}
      <div className="grid grid-cols-3 gap-3">
        <ReviewCoverageCard
          label="Item Review Coverage"
          value={formatCoveragePercentage(metrics.item_review_coverage_percentage)}
        />
        <ReviewCoverageCard
          label="Scene Review Coverage"
          value={formatCoveragePercentage(metrics.scene_review_coverage_percentage)}
        />
        <ReviewCoverageCard
          label="Hard-Failure Review Coverage"
          value={formatCoveragePercentage(metrics.hard_failure_review_coverage_percentage)}
        />
      </div>

      {/* Item Scores */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5">
        <h3 className="mb-3 text-base font-semibold text-zinc-800">Item Scores</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <ReviewCoverageCard label="Evaluations" value={item_scores.item_evaluation_count} />
          <ReviewCoverageCard label="Unique Outputs Reviewed" value={item_scores.unique_reviewed_output_count} />
          <ReviewCoverageCard
            label="Reviewers per Output"
            value={formatNullableMetric(item_scores.average_reviewers_per_reviewed_output)}
          />
          <ReviewCoverageCard
            label="Average Total"
            value={formatNullableMetric(item_scores.average_total)}
            suffix="/ 100"
          />
        </div>

        {Object.keys(item_scores.average_per_criterion).length > 0 && (
          <div className="mt-4">
            <p className="mb-2 text-sm font-medium text-zinc-600">Criterion Averages</p>
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-200 text-xs text-zinc-400">
                  <th className="py-1 pr-4 text-left font-medium">Criterion</th>
                  <th className="py-1 pr-4 text-right font-medium">Mean</th>
                  <th className="py-1 text-right font-medium">Std</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(item_scores.average_per_criterion).map(([key, stats]) => (
                  <CriterionRow key={key} name={key} stats={stats} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        <BreakdownTable data={item_scores.by_scene} title="By Scene" />
        <BreakdownTable data={item_scores.by_genre} title="By Genre" />
        <BreakdownTable data={item_scores.by_content_type} title="By Content Type" />
        <BreakdownTable data={item_scores.by_reviewer} title="By Reviewer" />

        {item_scores.requires_previous_memory && item_scores.no_previous_memory && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            <BreakdownTable data={item_scores.requires_previous_memory} title="Memory-dependent" />
            <BreakdownTable data={item_scores.no_previous_memory} title="No Previous Memory" />
          </div>
        )}
      </div>

      {/* Scene Scores */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5">
        <h3 className="mb-3 text-base font-semibold text-zinc-800">Scene Scores</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <ReviewCoverageCard label="Evaluations" value={scene_scores.scene_evaluation_count} />
          <ReviewCoverageCard label="Unique Scenes Reviewed" value={scene_scores.unique_reviewed_scenes} />
          <ReviewCoverageCard
            label="Coverage"
            value={formatCoveragePercentage(scene_scores.scene_review_coverage_percentage)}
          />
          <ReviewCoverageCard
            label="Average Total"
            value={formatNullableMetric(scene_scores.average_total)}
            suffix="/ 100"
          />
        </div>

        {Object.keys(scene_scores.average_per_criterion).length > 0 && (
          <div className="mt-4">
            <p className="mb-2 text-sm font-medium text-zinc-600">Criterion Averages</p>
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-200 text-xs text-zinc-400">
                  <th className="py-1 pr-4 text-left font-medium">Criterion</th>
                  <th className="py-1 pr-4 text-right font-medium">Mean</th>
                  <th className="py-1 text-right font-medium">Std</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(scene_scores.average_per_criterion).map(([key, stats]) => (
                  <CriterionRow key={key} name={key} stats={stats} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        <BreakdownTable data={scene_scores.by_reviewer} title="By Reviewer" />
      </div>

      {/* Hard-Failure Metrics */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5">
        <h3 className="mb-3 text-base font-semibold text-zinc-800">Hard-Failure Metrics</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <ReviewCoverageCard label="Reviews" value={hard_failures.hard_failure_review_count} />
          <ReviewCoverageCard
            label="Unique Outputs Reviewed"
            value={hard_failures.unique_outputs_reviewed_for_hard_failures}
          />
          <ReviewCoverageCard
            label="Outputs with Any Failure"
            value={hard_failures.outputs_with_any_hard_failure}
          />
          <ReviewCoverageCard
            label="Failure Rate"
            value={formatHardFailureRatePercentage(hard_failures.hard_failure_rate_among_reviewed_outputs, 1)}
          />
        </div>

        {Object.keys(hard_failures.count_per_flag).length > 0 && (
          <div className="mt-4">
            <p className="mb-2 text-sm font-medium text-zinc-600">Count per Flag</p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {Object.entries(hard_failures.count_per_flag).map(([key, count]) => (
                <div
                  key={key}
                  className="flex items-center justify-between rounded-lg border border-zinc-100 bg-zinc-50 px-3 py-2 text-xs"
                >
                  <span className="text-zinc-600">{key.replace(/_/g, " ")}</span>
                  <span className="ml-2 font-semibold text-zinc-800">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500">By Scene</p>
            <table className="w-full">
              <tbody>
                {Object.entries(hard_failures.by_scene).map(([key, count]) => (
                  <tr key={key} className="border-b border-zinc-100 text-xs">
                    <td className="py-1 pr-4 text-zinc-700">{key}</td>
                    <td className="py-1 text-right text-zinc-600">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500">By Genre</p>
            <table className="w-full">
              <tbody>
                {Object.entries(hard_failures.by_genre).map(([key, count]) => (
                  <tr key={key} className="border-b border-zinc-100 text-xs">
                    <td className="py-1 pr-4 text-zinc-700">{key}</td>
                    <td className="py-1 text-right text-zinc-600">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <p className="mb-1 text-xs font-medium text-zinc-500">By Content Type</p>
            <table className="w-full">
              <tbody>
                {Object.entries(hard_failures.by_content_type).map(([key, count]) => (
                  <tr key={key} className="border-b border-zinc-100 text-xs">
                    <td className="py-1 pr-4 text-zinc-700">{key}</td>
                    <td className="py-1 text-right text-zinc-600">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <ReviewCoverageCard label="Memory-dependent Failures" value={hard_failures.requires_previous_memory} />
          <ReviewCoverageCard label="No Previous Memory" value={hard_failures.no_previous_memory} />
        </div>

        {Object.keys(hard_failures.by_reviewer).length > 0 && (
          <div className="mt-4">
            <p className="mb-1 text-xs font-medium text-zinc-500">By Reviewer</p>
            <table className="w-full">
              <tbody>
                {Object.entries(hard_failures.by_reviewer).map(([key, count]) => (
                  <tr key={key} className="border-b border-zinc-100 text-xs">
                    <td className="py-1 pr-4 text-zinc-700">{key}</td>
                    <td className="py-1 text-right text-zinc-600">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
