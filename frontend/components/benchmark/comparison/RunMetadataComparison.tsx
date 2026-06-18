"use client"

import type { BenchmarkCompareEntry } from "@/types/benchmark"

interface Props {
  entry: BenchmarkCompareEntry
  label: string
}

export default function RunMetadataComparison({ entry, label }: Props) {
  const pct = (v: number) => `${(v * 100).toFixed(1)}%`

  return (
    <div className="space-y-2 text-xs">
      <p className="font-semibold text-zinc-800">{label}</p>
      <Row k="Run ID" v={String(entry.run_id)} />
      <Row k="Status" v={entry.status} />
      <Row k="Provider" v={entry.provider || "—"} />
      <Row k="Model" v={entry.model || "—"} />
      <Row k="Prompt Version" v={entry.prompt_version || "—"} />
      <Row k="Memory Gap" v={entry.memory_gap ? "Yes" : "No"} />
      <Row k="Item Coverage" v={pct(entry.item_review_coverage_percentage)} />
      <Row k="Scene Coverage" v={pct(entry.scene_review_coverage_percentage)} />
      <Row k="HF Coverage" v={pct(entry.hard_failure_review_coverage_percentage)} />
      {entry.coverage_note && (
        <div className="mt-2 rounded-md bg-amber-50 px-2 py-1.5 text-xs text-amber-700">
          {entry.coverage_note}
        </div>
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
