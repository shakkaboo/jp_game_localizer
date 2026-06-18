"use client"

import { useState, useEffect } from "react"
import type { BenchmarkHardFailureRead } from "@/types/benchmark"

interface Props {
  defaultValues: {
    invented_plot_information: boolean
    missing_critical_meaning: boolean
    wrong_speaker: boolean
    broken_placeholder: boolean
    major_glossary_violation: boolean
    contradiction_with_previous_scene: boolean
    unjustified_untranslated_japanese: boolean
    explanation: string | null
  }
  existingFailure: BenchmarkHardFailureRead | null
  onSave: (values: {
    invented_plot_information: boolean
    missing_critical_meaning: boolean
    wrong_speaker: boolean
    broken_placeholder: boolean
    major_glossary_violation: boolean
    contradiction_with_previous_scene: boolean
    unjustified_untranslated_japanese: boolean
    explanation: string | null
  }) => Promise<void>
  onDirtyChange: (dirty: boolean) => void
}

const FLAGS = [
  { key: "invented_plot_information", label: "Invented Plot Information" },
  { key: "missing_critical_meaning", label: "Missing Critical Meaning" },
  { key: "wrong_speaker", label: "Wrong Speaker" },
  { key: "broken_placeholder", label: "Broken Placeholder" },
  { key: "major_glossary_violation", label: "Major Glossary Violation" },
  { key: "contradiction_with_previous_scene", label: "Contradiction with Previous Scene" },
  { key: "unjustified_untranslated_japanese", label: "Unjustified Untranslated Japanese" },
] as const

export default function HardFailureForm({
  defaultValues,
  existingFailure,
  onSave,
  onDirtyChange,
}: Props) {
  const [flags, setFlags] = useState({
    invented_plot_information: defaultValues.invented_plot_information,
    missing_critical_meaning: defaultValues.missing_critical_meaning,
    wrong_speaker: defaultValues.wrong_speaker,
    broken_placeholder: defaultValues.broken_placeholder,
    major_glossary_violation: defaultValues.major_glossary_violation,
    contradiction_with_previous_scene: defaultValues.contradiction_with_previous_scene,
    unjustified_untranslated_japanese: defaultValues.unjustified_untranslated_japanese,
  })
  const [explanation, setExplanation] = useState(defaultValues.explanation || "")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const anyFlagged = Object.values(flags).some(Boolean)

  type FlagKey = keyof typeof flags

  const toggleFlag = (key: FlagKey) => {
    setFlags((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const getValues = (): {
    invented_plot_information: boolean
    missing_critical_meaning: boolean
    wrong_speaker: boolean
    broken_placeholder: boolean
    major_glossary_violation: boolean
    contradiction_with_previous_scene: boolean
    unjustified_untranslated_japanese: boolean
    explanation: string | null
  } => ({
    invented_plot_information: flags.invented_plot_information,
    missing_critical_meaning: flags.missing_critical_meaning,
    wrong_speaker: flags.wrong_speaker,
    broken_placeholder: flags.broken_placeholder,
    major_glossary_violation: flags.major_glossary_violation,
    contradiction_with_previous_scene: flags.contradiction_with_previous_scene,
    unjustified_untranslated_japanese: flags.unjustified_untranslated_japanese,
    explanation: explanation || null,
  })

  const isDirty = !(
    flags.invented_plot_information === (existingFailure?.invented_plot_information ?? false) &&
    flags.missing_critical_meaning === (existingFailure?.missing_critical_meaning ?? false) &&
    flags.wrong_speaker === (existingFailure?.wrong_speaker ?? false) &&
    flags.broken_placeholder === (existingFailure?.broken_placeholder ?? false) &&
    flags.major_glossary_violation === (existingFailure?.major_glossary_violation ?? false) &&
    flags.contradiction_with_previous_scene === (existingFailure?.contradiction_with_previous_scene ?? false) &&
    flags.unjustified_untranslated_japanese === (existingFailure?.unjustified_untranslated_japanese ?? false) &&
    (explanation || null) === (existingFailure?.explanation ?? null)
  )

  useEffect(() => {
    onDirtyChange(isDirty)
  }, [isDirty, onDirtyChange])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      await onSave(getValues())
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-zinc-700">Hard-Failure Review</h3>

      {!anyFlagged && (
        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          Reviewed — no hard failure found
        </div>
      )}

      <div className="grid gap-2 sm:grid-cols-2">
        {FLAGS.map((f) => (
          <label
            key={f.key}
            className="flex cursor-pointer items-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
          >
            <input
              type="checkbox"
              checked={flags[f.key]}
              onChange={() => toggleFlag(f.key)}
              className="h-4 w-4 rounded border-zinc-300"
            />
            {f.label}
          </label>
        ))}
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-zinc-800">Explanation</label>
        <textarea
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-800"
        />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <button
        type="button"
        onClick={handleSave}
        disabled={saving || !isDirty}
        className="rounded-lg bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-40"
      >
        {saving ? "Saving..." : existingFailure ? "Update Hard-Failure Review" : "Submit Hard-Failure Review"}
      </button>
    </div>
  )
}
