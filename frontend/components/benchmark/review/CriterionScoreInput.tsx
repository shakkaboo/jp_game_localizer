"use client"

interface Props {
  label: string
  description: string
  value: number
  maximum: number
  onChange: (value: number) => void
  disabled?: boolean
  error?: string
}

export default function CriterionScoreInput({
  label,
  description,
  value,
  maximum,
  onChange,
  disabled = false,
  error,
}: Props) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value
    if (raw === "") {
      onChange(0)
      return
    }
    const parsed = parseInt(raw, 10)
    if (isNaN(parsed)) return
    const clamped = Math.max(0, Math.min(maximum, parsed))
    onChange(clamped)
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div>
          <label className="text-sm font-medium text-zinc-800">{label}</label>
          <p className="text-xs text-zinc-400">{description}</p>
        </div>
        <span className="text-sm font-semibold text-zinc-600">
          {value} / {maximum}
        </span>
      </div>
      <input
        type="number"
        min={0}
        max={maximum}
        value={value}
        onChange={handleChange}
        disabled={disabled}
        className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-800 disabled:opacity-50"
      />
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  )
}
