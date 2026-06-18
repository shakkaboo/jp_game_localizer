"use client"

interface Props {
  onPrev: () => void
  onNext: () => void
  currentIndex: number
  totalItems: number
  onJumpToFirstUnreviewed: () => void
  hasUnreviewedItems: boolean
  onSceneChange: (sceneNumber: number) => void
  scenes: { sceneNumber: number; title: string | null }[]
  currentSceneNumber: number
  isDirty: boolean
}

export default function ReviewNavigation({
  onPrev,
  onNext,
  currentIndex,
  totalItems,
  onJumpToFirstUnreviewed,
  hasUnreviewedItems,
  onSceneChange,
  scenes,
  currentSceneNumber,
  isDirty,
}: Props) {
  const handlePrev = () => {
    if (isDirty && !confirm("You have unsaved changes. Discard them and navigate away?")) return
    onPrev()
  }

  const handleNext = () => {
    if (isDirty && !confirm("You have unsaved changes. Discard them and navigate away?")) return
    onNext()
  }

  const handleSceneChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (isDirty && !confirm("You have unsaved changes. Discard them and navigate away?")) return
    onSceneChange(Number(e.target.value))
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={handlePrev}
        disabled={currentIndex <= 0}
        className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:opacity-40"
      >
        &larr; Prev
      </button>

      <span className="text-sm text-zinc-500">
        {currentIndex + 1} / {totalItems}
      </span>

      <button
        type="button"
        onClick={handleNext}
        disabled={currentIndex >= totalItems - 1}
        className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:opacity-40"
      >
        Next &rarr;
      </button>

      {hasUnreviewedItems && (
        <button
          type="button"
          onClick={() => {
            if (isDirty && !confirm("You have unsaved changes. Discard them and navigate away?")) return
            onJumpToFirstUnreviewed()
          }}
          className="rounded-lg border border-purple-300 bg-purple-50 px-3 py-1.5 text-sm font-medium text-purple-700 transition-colors hover:bg-purple-100"
        >
          Jump to unreviewed
        </button>
      )}

      <select
        value={currentSceneNumber}
        onChange={handleSceneChange}
        className="ml-auto rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-700"
      >
        {scenes.map((s) => (
          <option key={s.sceneNumber} value={s.sceneNumber}>
            Scene {s.sceneNumber}: {s.title || `Scene ${s.sceneNumber}`}
          </option>
        ))}
      </select>
    </div>
  )
}
