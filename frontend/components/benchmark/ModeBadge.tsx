interface Props {
  mode: string
}

const LABELS: Record<string, string> = {
  plain: "Plain",
  context: "Context",
  context_memory: "Ctx+Mem",
}

const COLORS: Record<string, string> = {
  plain: "bg-gray-100 text-gray-700 border-gray-200",
  context: "bg-blue-50 text-blue-700 border-blue-200",
  context_memory: "bg-purple-50 text-purple-700 border-purple-200",
}

export default function ModeBadge({ mode }: Props) {
  const label = LABELS[mode] || mode
  const cls = COLORS[mode] || "bg-zinc-50 text-zinc-600 border-zinc-200"
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${cls}`}
    >
      {label}
    </span>
  )
}
