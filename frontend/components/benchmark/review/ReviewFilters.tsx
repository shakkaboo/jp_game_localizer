"use client"

interface FilterOption {
  key: string
  label: string
}

interface Props {
  filters: FilterOption[]
  activeFilter: string
  onFilterChange: (key: string) => void
  isDirty: boolean
}

export default function ReviewFilters({
  filters,
  activeFilter,
  onFilterChange,
  isDirty,
}: Props) {
  const handleChange = (key: string) => {
    if (isDirty && !confirm("You have unsaved changes. Discard them and navigate away?")) return
    onFilterChange(key)
  }

  return (
    <div className="flex flex-wrap gap-2">
      {filters.map((f) => (
        <button
          key={f.key}
          type="button"
          onClick={() => handleChange(f.key)}
          className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
            activeFilter === f.key
              ? "border-zinc-800 bg-zinc-800 text-white"
              : "border-zinc-300 bg-white text-zinc-600 hover:bg-zinc-50"
          }`}
        >
          {f.label}
        </button>
      ))}
    </div>
  )
}
