interface Props {
  status: string
}

export default function StatusBadge({ status }: Props) {
  const colors: Record<string, string> = {
    pending: "bg-amber-50 text-amber-700 border-amber-200",
    translated: "bg-green-50 text-green-700 border-green-200",
    draft: "bg-blue-50 text-blue-700 border-blue-200",
  }

  const cls = colors[status] || "bg-zinc-50 text-zinc-600 border-zinc-200"

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${cls}`}
    >
      {status}
    </span>
  )
}
