import Link from "next/link"
import type { BenchmarkDatasetListItem, BenchmarkRunRead } from "@/types/benchmark"
import ModeBadge from "./ModeBadge"
import StatusBadge from "./StatusBadge"

interface Props {
  dataset: BenchmarkDatasetListItem
  latestRuns: BenchmarkRunRead[]
}

export default function DatasetCard({ dataset, latestRuns }: Props) {
  const latestByMode: Record<string, BenchmarkRunRead | undefined> = {}
  for (const run of latestRuns) {
    if (!latestByMode[run.mode] || run.id > latestByMode[run.mode]!.id) {
      latestByMode[run.mode] = run
    }
  }

  return (
    <Link
      href={`/benchmark/datasets/${dataset.id}`}
      className="block rounded-xl border border-zinc-200 bg-white p-5 transition-colors hover:border-zinc-300"
    >
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-zinc-900">{dataset.name}</h3>
          <p className="text-sm text-zinc-500">v{dataset.version}</p>
        </div>
        <StatusBadge status={dataset.review_status} />
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-lg bg-zinc-50 px-3 py-2">
          <p className="text-xs text-zinc-500">Scenes</p>
          <p className="font-semibold text-zinc-800">{dataset.scene_count}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 px-3 py-2">
          <p className="text-xs text-zinc-500">Items</p>
          <p className="font-semibold text-zinc-800">{dataset.item_count}</p>
        </div>
      </div>

      {latestRuns.length > 0 && (
        <div className="space-y-1.5 border-t border-zinc-100 pt-3">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
            Latest Runs
          </p>
          {(["plain", "context", "context_memory"] as const).map((mode) => {
            const run = latestByMode[mode]
            if (!run) return null
            return (
              <Link
                key={run.id}
                href={`/benchmark/runs/${run.id}`}
                className="flex items-center gap-2 rounded-md px-2 py-1 text-sm hover:bg-zinc-50"
                onClick={(e) => e.stopPropagation()}
              >
                <ModeBadge mode={run.mode} />
                <StatusBadge status={run.status} />
                <span className="ml-auto text-xs text-zinc-400">
                  #{run.id}
                </span>
              </Link>
            )
          })}
        </div>
      )}
    </Link>
  )
}
