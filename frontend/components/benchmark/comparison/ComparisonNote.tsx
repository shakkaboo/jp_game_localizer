"use client"

interface Props {
  note: string
}

export default function ComparisonNote({ note }: Props) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm text-zinc-500">
      {note}
    </div>
  )
}
