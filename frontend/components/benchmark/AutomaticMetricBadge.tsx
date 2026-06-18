interface Props {
  label: string
  value: number | boolean | null | undefined
  verbose?: boolean
}

function formatValue(value: number | boolean | null | undefined): string {
  if (value === null || value === undefined) return "—"
  if (typeof value === "boolean") return value ? "Yes" : "No"
  if (typeof value === "number") return String(Math.round(value * 100) / 100)
  return String(value)
}

function badgeColor(
  label: string,
  value: number | boolean | null | undefined
): string {
  if (value === null || value === undefined) return "bg-zinc-50 text-zinc-400 border-zinc-200"
  if (typeof value === "boolean") {
    return value
      ? "bg-red-50 text-red-700 border-red-200"
      : "bg-green-50 text-green-700 border-green-200"
  }
  if (label === "chrF" || label === "BLEU") {
    if (value >= 80) return "bg-green-50 text-green-700 border-green-200"
    if (value >= 50) return "bg-amber-50 text-amber-700 border-amber-200"
    return "bg-red-50 text-red-700 border-red-200"
  }
  return "bg-zinc-50 text-zinc-600 border-zinc-200"
}

export default function AutomaticMetricBadge({ label, value, verbose }: Props) {
  const cls = badgeColor(label, value)
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${cls}`}
      title={verbose ? `${label}: ${formatValue(value)}` : undefined}
    >
      {!verbose && <span className="text-zinc-400">{label}</span>}
      {formatValue(value)}
    </span>
  )
}
