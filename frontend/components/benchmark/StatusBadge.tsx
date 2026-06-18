interface Props {
  status: string
}

const COLORS: Record<string, string> = {
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  running: "bg-blue-50 text-blue-700 border-blue-200",
  completed: "bg-green-50 text-green-700 border-green-200",
  completed_with_errors: "bg-orange-50 text-orange-700 border-orange-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  missing: "bg-zinc-50 text-zinc-400 border-zinc-200",
}

export default function StatusBadge({ status }: Props) {
  const cls = COLORS[status] || "bg-zinc-50 text-zinc-600 border-zinc-200"
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${cls}`}
    >
      {status.replace(/_/g, " ")}
    </span>
  )
}
