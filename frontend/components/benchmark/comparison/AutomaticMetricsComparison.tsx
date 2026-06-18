"use client"

import type { BenchmarkMetricsSummary } from "@/types/benchmark"
import { formatNullableMetric } from "@/lib/benchmark-helpers"

interface Props {
  autoMetrics: BenchmarkMetricsSummary | null
  label: string
}

export default function AutomaticMetricsComparison({ autoMetrics, label }: Props) {
  if (!autoMetrics) {
    return (
      <div className="space-y-2 text-xs">
        <p className="font-semibold text-zinc-800">{label}</p>
        <p className="text-zinc-400 italic">No automatic metrics</p>
      </div>
    )
  }

  return (
    <div className="space-y-2 text-xs">
      <p className="font-semibold text-zinc-800">{label}</p>
      <Row k="chrF" v={formatNullableMetric(autoMetrics.chrf?.mean ?? null)} />
      <Row k="BLEU" v={formatNullableMetric(autoMetrics.bleu?.mean ?? null)} />
      <Row k="Glossary Compliance" v={formatNullableMetric(autoMetrics.glossary_compliance_rate, 1)} />
      <Row k="Placeholder Preservation" v={formatNullableMetric(autoMetrics.placeholder_preservation_rate, 1)} />
      <Row k="Missing Outputs" v={String(autoMetrics.missing_output_count)} />
      <Row k="Untranslated JP" v={String(autoMetrics.untranslated_japanese_count)} />
      <Row k="Line ID Mismatch" v={String(autoMetrics.line_id_mismatch_count)} />
      <Row k="Speaker Mismatch" v={String(autoMetrics.speaker_mismatch_count)} />
      {autoMetrics.requires_previous_memory && (
        <Row
          k="Memory-dep chrF"
          v={formatNullableMetric(autoMetrics.requires_previous_memory.mean_chrf)}
        />
      )}
      {autoMetrics.no_previous_memory && (
        <Row
          k="No-memory chrF"
          v={formatNullableMetric(autoMetrics.no_previous_memory.mean_chrf)}
        />
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
