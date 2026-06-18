"use client"

interface Props {
  warnings: string[]
}

export default function ComparisonWarnings({ warnings }: Props) {
  if (warnings.length === 0) return null

  return (
    <div className="space-y-2 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
      <p className="text-sm font-semibold text-amber-800">Warnings</p>
      {warnings.map((w, i) => (
        <p key={i} className="text-sm text-amber-700">
          &bull; {w}
        </p>
      ))}
    </div>
  )
}
