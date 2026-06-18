"use client"

import type { BenchmarkCompareEntry } from "@/types/benchmark"
import { formatCoveragePercentage } from "@/lib/benchmark-helpers"

interface Props {
  entries: BenchmarkCompareEntry[]
}

type CoverageKey =
  | "item_review_coverage_percentage"
  | "scene_review_coverage_percentage"
  | "hard_failure_review_coverage_percentage"

const coverageKeys: { key: CoverageKey }[] = [
  { key: "item_review_coverage_percentage" },
  { key: "scene_review_coverage_percentage" },
  { key: "hard_failure_review_coverage_percentage" },
]

export default function CoverageComparison({ entries }: Props) {
  if (entries.length === 0) return null

  const labels = ["Plain", "Context", "Context + Memory"]

  return (
    <div className="space-y-2 text-xs">
      <p className="font-semibold text-zinc-700">Coverage</p>
      <div className="grid grid-cols-3 gap-2">
        {coverageKeys.map(({ key }) => (
          <div key={key} className="rounded-lg border border-zinc-200 bg-white p-2">
            <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-zinc-400">
              {key.replace(/_/g, " ")}
            </p>
            {entries.map((e, i) => (
              <div key={e.run_id} className="flex justify-between text-xs">
                <span className="text-zinc-500">{labels[i] || e.mode}</span>
                <span className="font-medium text-zinc-800">
                  {formatCoveragePercentage(e[key])}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
