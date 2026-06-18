"use client"

import { useState, useEffect } from "react"
import CriterionScoreInput from "./CriterionScoreInput"
import type { BenchmarkSceneEvaluationRead } from "@/types/benchmark"

interface Props {
  defaultValues: {
    voice_consistency: number
    terminology_consistency: number
    emotional_progression: number
    relationship_continuity: number
    narrative_coherence: number
    genre_tone_consistency: number
    reviewer_notes: string | null
  }
  existingEvaluation: BenchmarkSceneEvaluationRead | null
  onSave: (values: {
    voice_consistency: number
    terminology_consistency: number
    emotional_progression: number
    relationship_continuity: number
    narrative_coherence: number
    genre_tone_consistency: number
    reviewer_notes: string | null
  }) => Promise<void>
  onDirtyChange: (dirty: boolean) => void
}

const TOTAL_MAX = 100

export default function SceneReviewForm({
  defaultValues,
  existingEvaluation,
  onSave,
  onDirtyChange,
}: Props) {
  const [voice_consistency, setVoiceConsistency] = useState(defaultValues.voice_consistency)
  const [terminology_consistency, setTerminologyConsistency] = useState(defaultValues.terminology_consistency)
  const [emotional_progression, setEmotionalProgression] = useState(defaultValues.emotional_progression)
  const [relationship_continuity, setRelationshipContinuity] = useState(defaultValues.relationship_continuity)
  const [narrative_coherence, setNarrativeCoherence] = useState(defaultValues.narrative_coherence)
  const [genre_tone_consistency, setGenreToneConsistency] = useState(defaultValues.genre_tone_consistency)
  const [reviewer_notes, setReviewerNotes] = useState(defaultValues.reviewer_notes || "")

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const previewTotal =
    voice_consistency +
    terminology_consistency +
    emotional_progression +
    relationship_continuity +
    narrative_coherence +
    genre_tone_consistency

  const getValues = () => ({
    voice_consistency,
    terminology_consistency,
    emotional_progression,
    relationship_continuity,
    narrative_coherence,
    genre_tone_consistency,
    reviewer_notes: reviewer_notes || null,
  })

  const isDirty = !(
    voice_consistency === (existingEvaluation?.voice_consistency ?? 0) &&
    terminology_consistency === (existingEvaluation?.terminology_consistency ?? 0) &&
    emotional_progression === (existingEvaluation?.emotional_progression ?? 0) &&
    relationship_continuity === (existingEvaluation?.relationship_continuity ?? 0) &&
    narrative_coherence === (existingEvaluation?.narrative_coherence ?? 0) &&
    genre_tone_consistency === (existingEvaluation?.genre_tone_consistency ?? 0) &&
    reviewer_notes === (existingEvaluation?.reviewer_notes ?? "")
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
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-700">Scene Review Scores</h3>
        <span className="text-sm text-zinc-500">
          Preview: {previewTotal} / {TOTAL_MAX}
          {existingEvaluation && (
            <span className="ml-2 text-green-600">Saved: {existingEvaluation.total_score} / {TOTAL_MAX}</span>
          )}
        </span>
      </div>

      <CriterionScoreInput
        label="Voice Consistency"
        description="Consistent character voice across scenes"
        value={voice_consistency}
        maximum={25}
        onChange={setVoiceConsistency}
      />
      <CriterionScoreInput
        label="Terminology Consistency"
        description="Consistent term usage"
        value={terminology_consistency}
        maximum={20}
        onChange={setTerminologyConsistency}
      />
      <CriterionScoreInput
        label="Emotional Progression"
        description="Emotional arc maintained"
        value={emotional_progression}
        maximum={15}
        onChange={setEmotionalProgression}
      />
      <CriterionScoreInput
        label="Relationship Continuity"
        description="Relationships stay consistent"
        value={relationship_continuity}
        maximum={15}
        onChange={setRelationshipContinuity}
      />
      <CriterionScoreInput
        label="Narrative Coherence"
        description="Story flows logically"
        value={narrative_coherence}
        maximum={15}
        onChange={setNarrativeCoherence}
      />
      <CriterionScoreInput
        label="Genre/Tone Consistency"
        description="Consistent genre and tone"
        value={genre_tone_consistency}
        maximum={10}
        onChange={setGenreToneConsistency}
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
        {saving ? "Saving..." : existingEvaluation ? "Update Scene Review" : "Submit Scene Review"}
      </button>
    </div>
  )
}
