"use client"

import type { BenchmarkCompareEntry } from "@/types/benchmark"
import RunMetadataComparison from "./RunMetadataComparison"
import AutomaticMetricsComparison from "./AutomaticMetricsComparison"
import HumanItemMetricsComparison from "./HumanItemMetricsComparison"
import HumanSceneMetricsComparison from "./HumanSceneMetricsComparison"
import HardFailureMetricsComparison from "./HardFailureMetricsComparison"
import CoverageComparison from "./CoverageComparison"

interface Props {
  entries: BenchmarkCompareEntry[]
}

const LABELS = ["Plain", "Context", "Context + Memory"]

export default function ComparisonTable({ entries }: Props) {
  if (entries.length === 0) return null

  const labelFor = (entry: BenchmarkCompareEntry, i: number): string =>
    LABELS[i] || entry.mode

  return (
    <div className="overflow-x-auto">
      <div className="grid min-w-[600px] grid-cols-3 gap-4">
        {/* Run Metadata */}
        <SectionHeader title="Run Metadata" />
        {entries.map((e, i) => (
          <RunMetadataComparison key={e.run_id} entry={e} label={labelFor(e, i)} />
        ))}

        <div className="col-span-3 border-t border-zinc-200 pt-4" />

        {/* Coverage */}
        <div className="col-span-3">
          <CoverageComparison entries={entries} />
        </div>

        <div className="col-span-3 border-t border-zinc-200 pt-4" />

        {/* Automatic Metrics */}
        <SectionHeader title="Automatic Metrics" />
        {entries.map((e, i) => (
          <AutomaticMetricsComparison
            key={e.run_id}
            autoMetrics={e.automatic_metrics}
            label={labelFor(e, i)}
          />
        ))}

        <div className="col-span-3 border-t border-zinc-200 pt-4" />

        {/* Human Item Metrics */}
        <SectionHeader title="Human Item Metrics" />
        {entries.map((e, i) => (
          <HumanItemMetricsComparison
            key={e.run_id}
            humanMetrics={e.human_metrics}
            label={labelFor(e, i)}
          />
        ))}

        <div className="col-span-3 border-t border-zinc-200 pt-4" />

        {/* Human Scene Metrics */}
        <SectionHeader title="Human Scene Metrics" />
        {entries.map((e, i) => (
          <HumanSceneMetricsComparison
            key={e.run_id}
            humanMetrics={e.human_metrics}
            label={labelFor(e, i)}
          />
        ))}

        <div className="col-span-3 border-t border-zinc-200 pt-4" />

        {/* Hard-Failure Metrics */}
        <SectionHeader title="Hard-Failure Metrics" />
        {entries.map((e, i) => (
          <HardFailureMetricsComparison
            key={e.run_id}
            humanMetrics={e.human_metrics}
            label={labelFor(e, i)}
          />
        ))}
      </div>
    </div>
  )
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div className="col-span-3">
      <h3 className="text-sm font-semibold text-zinc-700">{title}</h3>
    </div>
  )
}
