"use client"

interface Props {
  label: string
  value: number | string | null | undefined
  suffix?: string
  subtext?: string
}

export default function ReviewCoverageCard({ label, value, suffix, subtext }: Props) {
  const displayValue = value === null || value === undefined ? "—" : value
  return (
    <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="mt-0.5 text-lg font-semibold text-zinc-800">
        {displayValue}
        {suffix && <span className="text-sm font-normal text-zinc-400"> {suffix}</span>}
      </p>
      {subtext && <p className="mt-0.5 text-xs text-zinc-400">{subtext}</p>}
    </div>
  )
}
