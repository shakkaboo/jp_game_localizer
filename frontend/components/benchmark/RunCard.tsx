import Link from "next/link"
import type { BenchmarkRunRead } from "@/types/benchmark"
import ModeBadge from "./ModeBadge"
import StatusBadge from "./StatusBadge"

interface Props {
  run: BenchmarkRunRead
}

export default function RunCard({ run }: Props) {
  return (
    <Link
      href={`/benchmark/runs/${run.id}`}
      className="block rounded-xl border border-zinc-200 bg-white p-4 transition-colors hover:border-zinc-300"
    >
      <div className="flex items-center gap-3">
        <ModeBadge mode={run.mode} />
        <StatusBadge status={run.status} />
        <span className="text-xs text-zinc-400">#{run.id}</span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-zinc-500">
        <span>
          {run.llm_provider} / {run.llm_model}
        </span>
        <span className="text-right">
          {run.completed_scenes}/{run.total_scenes} scenes
        </span>
      </div>
    </Link>
  )
}
