"use client"

import { useState, useEffect } from "react"
import CriterionScoreInput from "./CriterionScoreInput"
import type { BenchmarkItemEvaluationRead } from "@/types/benchmark"

interface Props {
  defaultValues: {
    meaning_preservation: number
    omission_addition_control: number
    natural_english: number
    character_voice: number
    glossary_consistency: number
    genre_tone_fit: number
    scene_consistency: number
    grammar_punctuation: number
    reviewer_notes: string | null
  }
  existingEvaluation: BenchmarkItemEvaluationRead | null
  outputStatus: string
  onSave: (values: {
    meaning_preservation: number
    omission_addition_control: number
    natural_english: number
    character_voice: number
    glossary_consistency: number
    genre_tone_fit: number
    scene_consistency: number
    grammar_punctuation: number
    reviewer_notes: string | null
  }) => Promise<void>
  onDirtyChange: (dirty: boolean) => void
}

const TOTAL_MAX = 100

export default function ItemReviewForm({
  defaultValues,
  existingEvaluation,
  outputStatus,
  onSave,
  onDirtyChange,
}: Props) {
  const [meaning_preservation, setMeaningPreservation] = useState(defaultValues.meaning_preservation)
  const [omission_addition_control, setOmissionAdditionControl] = useState(defaultValues.omission_addition_control)
  const [natural_english, setNaturalEnglish] = useState(defaultValues.natural_english)
  const [character_voice, setCharacterVoice] = useState(defaultValues.character_voice)
  const [glossary_consistency, setGlossaryConsistency] = useState(defaultValues.glossary_consistency)
  const [genre_tone_fit, setGenreToneFit] = useState(defaultValues.genre_tone_fit)
  const [scene_consistency, setSceneConsistency] = useState(defaultValues.scene_consistency)
  const [grammar_punctuation, setGrammarPunctuation] = useState(defaultValues.grammar_punctuation)
  const [reviewer_notes, setReviewerNotes] = useState(defaultValues.reviewer_notes || "")

  const [saving, setSaving] = useState(false)
  const [savedTotal, setSavedTotal] = useState<number | null>(
    existingEvaluation?.total_score ?? null
  )
  const [error, setError] = useState<string | null>(null)

  const previewTotal =
    meaning_preservation +
    omission_addition_control +
    natural_english +
    character_voice +
    glossary_consistency +
    genre_tone_fit +
    scene_consistency +
    grammar_punctuation

  const isCompleted = outputStatus === "completed"

  const getValues = () => ({
    meaning_preservation,
    omission_addition_control,
    natural_english,
    character_voice,
    glossary_consistency,
    genre_tone_fit,
    scene_consistency,
    grammar_punctuation,
    reviewer_notes: reviewer_notes || null,
  })

  const valuesEqual = (
    a: ReturnType<typeof getValues>,
    b: ReturnType<typeof getValues>
  ): boolean => {
    return (
      a.meaning_preservation === b.meaning_preservation &&
      a.omission_addition_control === b.omission_addition_control &&
      a.natural_english === b.natural_english &&
      a.character_voice === b.character_voice &&
      a.glossary_consistency === b.glossary_consistency &&
      a.genre_tone_fit === b.genre_tone_fit &&
      a.scene_consistency === b.scene_consistency &&
      a.grammar_punctuation === b.grammar_punctuation &&
      a.reviewer_notes === b.reviewer_notes
    )
  }

  const isDirty = !valuesEqual(getValues(), {
    meaning_preservation: existingEvaluation?.meaning_preservation ?? 0,
    omission_addition_control: existingEvaluation?.omission_addition_control ?? 0,
    natural_english: existingEvaluation?.natural_english ?? 0,
    character_voice: existingEvaluation?.character_voice ?? 0,
    glossary_consistency: existingEvaluation?.glossary_consistency ?? 0,
    genre_tone_fit: existingEvaluation?.genre_tone_fit ?? 0,
    scene_consistency: existingEvaluation?.scene_consistency ?? 0,
    grammar_punctuation: existingEvaluation?.grammar_punctuation ?? 0,
    reviewer_notes: existingEvaluation?.reviewer_notes ?? null,
  })

  useEffect(() => {
    onDirtyChange(isDirty)
  }, [isDirty, onDirtyChange])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      await onSave(getValues())
      setSavedTotal(previewTotal)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save")
    } finally {
      setSaving(false)
    }
  }

  if (!isCompleted) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
          <p className="text-sm text-zinc-500">
            Item review requires a completed output. This output status is{" "}
            <strong>{outputStatus}</strong>.
          </p>
          <p className="mt-1 text-xs text-zinc-400">
            Failed outputs may still receive a hard-failure review below.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-700">Item Review Scores</h3>
        <span className="text-sm text-zinc-500">
          Preview: {previewTotal} / {TOTAL_MAX}
          {savedTotal !== null && (
            <span className="ml-2 text-green-600">Saved: {savedTotal} / {TOTAL_MAX}</span>
          )}
        </span>
      </div>

      <CriterionScoreInput
        label="Meaning Preservation"
        description="Accuracy of meaning"
        value={meaning_preservation}
        maximum={25}
        onChange={setMeaningPreservation}
      />
      <CriterionScoreInput
        label="Omission/Addition Control"
        description="No missing or added content"
        value={omission_addition_control}
        maximum={15}
        onChange={setOmissionAdditionControl}
      />
      <CriterionScoreInput
        label="Natural English"
        description="Fluency and naturalness"
        value={natural_english}
        maximum={15}
        onChange={setNaturalEnglish}
      />
      <CriterionScoreInput
        label="Character Voice"
        description="Consistent character portrayal"
        value={character_voice}
        maximum={15}
        onChange={setCharacterVoice}
      />
      <CriterionScoreInput
        label="Glossary Consistency"
        description="Terms match glossary"
        value={glossary_consistency}
        maximum={10}
        onChange={setGlossaryConsistency}
      />
      <CriterionScoreInput
        label="Genre/Tone Fit"
        description="Appropriate for genre and tone"
        value={genre_tone_fit}
        maximum={10}
        onChange={setGenreToneFit}
      />
      <CriterionScoreInput
        label="Scene Consistency"
        description="Consistent within scene"
        value={scene_consistency}
        maximum={5}
        onChange={setSceneConsistency}
      />
      <CriterionScoreInput
        label="Grammar/Punctuation"
        description="Correct grammar and punctuation"
        value={grammar_punctuation}
        maximum={5}
        onChange={setGrammarPunctuation}
      />

      <div className="space-y-1">
        <label className="text-sm font-medium text-zinc-800">Reviewer Notes</label>
        <textarea
          value={reviewer_notes}
          onChange={(e) => setReviewerNotes(e.target.value)}
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
        {saving ? "Saving..." : existingEvaluation ? "Update Review" : "Submit Review"}
      </button>
    </div>
  )
}
