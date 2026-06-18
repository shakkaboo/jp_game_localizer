import type { BenchmarkMetricsSummary } from "@/types/benchmark"
import WarningBanner from "./WarningBanner"

interface Props {
  metrics: BenchmarkMetricsSummary
}

function formatRate(value: number | null): string {
  if (value === null) return "—"
  return `${(value * 100).toFixed(1)}%`
}

function formatChrf(value: number | null): string {
  if (value === null) return "—"
  return value.toFixed(2)
}

export default function MetricsSummary({ metrics }: Props) {
  return (
    <div className="space-y-6">
      <WarningBanner message="Automatic metrics are supporting signals and do not by themselves determine localization quality." />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          label="Status"
          value={metrics.status.replace(/_/g, " ")}
          highlight
        />
        <StatCard
          label="Completed Items"
          value={`${metrics.completed_items}/${metrics.total_items}`}
        />
        <StatCard label="Failed Items" value={String(metrics.failed_items)} />
        <StatCard
          label="Missing Output"
          value={String(metrics.missing_output_count)}
        />
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-400">
          Score Metrics
        </h3>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {metrics.chrf && (
            <>
              <StatCard
                label="chrF (mean)"
                value={formatChrf(metrics.chrf.mean ?? null)}
              />
              <StatCard
                label="chrF (std)"
                value={formatChrf(metrics.chrf.std ?? null)}
              />
              {metrics.chrf.min !== undefined && (
                <StatCard
                  label="chrF (min)"
                  value={formatChrf(metrics.chrf.min ?? null)}
                />
              )}
              {metrics.chrf.max !== undefined && (
                <StatCard
                  label="chrF (max)"
                  value={formatChrf(metrics.chrf.max ?? null)}
                />
              )}
            </>
          )}
          {metrics.bleu && (
            <>
              <StatCard
                label="BLEU (mean)"
                value={formatChrf(metrics.bleu.mean ?? null)}
              />
              <StatCard
                label="BLEU (std)"
                value={formatChrf(metrics.bleu.std ?? null)}
              />
            </>
          )}
          <StatCard
            label="Glossary Compliance"
            value={formatRate(metrics.glossary_compliance_rate)}
          />
          <StatCard
            label="Placeholder Preservation"
            value={formatRate(metrics.placeholder_preservation_rate)}
          />
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-400">
          Issue Counts
        </h3>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard
            label="Untranslated JP"
            value={String(metrics.untranslated_japanese_count)}
          />
          <StatCard
            label="Line ID Mismatch"
            value={String(metrics.line_id_mismatch_count)}
          />
          <StatCard
            label="Speaker Mismatch"
            value={String(metrics.speaker_mismatch_count)}
          />
        </div>
      </div>

      {metrics.requires_previous_memory && (
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-400">
            Memory Dependency
          </h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard
              label="Mem-dep count"
              value={String(metrics.requires_previous_memory.count)}
            />
            <StatCard
              label="Mem-dep chrF"
              value={formatChrf(metrics.requires_previous_memory.mean_chrf)}
            />
            {metrics.no_previous_memory && (
              <>
                <StatCard
                  label="No-mem count"
                  value={String(metrics.no_previous_memory.count)}
                />
                <StatCard
                  label="No-mem chrF"
                  value={formatChrf(metrics.no_previous_memory.mean_chrf)}
                />
              </>
            )}
          </div>
        </div>
      )}

      {Object.keys(metrics.per_genre).length > 0 && (
        <CategoryBreakdown
          title="Per Genre"
          data={metrics.per_genre}
        />
      )}
      {Object.keys(metrics.per_content_type).length > 0 && (
        <CategoryBreakdown
          title="Per Content Type"
          data={metrics.per_content_type}
        />
      )}
      {Object.keys(metrics.per_scene).length > 0 && (
        <CategoryBreakdown
          title="Per Scene"
          data={metrics.per_scene}
        />
      )}
    </div>
  )
}

function StatCard({
  label,
  value,
  highlight,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
      <p className="text-xs text-zinc-500">{label}</p>
      <p
        className={`mt-0.5 text-base font-semibold ${
          highlight ? "text-zinc-900" : "text-zinc-700"
        }`}
      >
        {value}
      </p>
    </div>
  )
}

function CategoryBreakdown({
  title,
  data,
}: {
  title: string
  data: Record<string, { count: number; mean_chrf: number | null }>
}) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-400">
        {title}
      </h3>
      <div className="overflow-x-auto rounded-xl border border-zinc-200">
        <table className="min-w-full divide-y divide-zinc-100 text-sm">
          <thead className="bg-zinc-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-zinc-500">
                Category
              </th>
              <th className="px-4 py-2 text-right font-medium text-zinc-500">
                Count
              </th>
              <th className="px-4 py-2 text-right font-medium text-zinc-500">
                Mean chrF
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {Object.entries(data).map(([key, val]) => (
              <tr key={key} className="hover:bg-zinc-50">
                <td className="px-4 py-2 font-medium text-zinc-800">{key}</td>
                <td className="px-4 py-2 text-right text-zinc-600">
                  {val.count}
                </td>
                <td className="px-4 py-2 text-right text-zinc-600">
                  {val.mean_chrf !== null ? val.mean_chrf.toFixed(2) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
