export function normalizeReviewerLabel(label: string): string {
  return label.trim().replace(/\s+/g, " ")
}

export function calculateItemPreviewTotal(values: {
  meaning_preservation: number
  omission_addition_control: number
  natural_english: number
  character_voice: number
  glossary_consistency: number
  genre_tone_fit: number
  scene_consistency: number
  grammar_punctuation: number
}): number {
  return (
    values.meaning_preservation +
    values.omission_addition_control +
    values.natural_english +
    values.character_voice +
    values.glossary_consistency +
    values.genre_tone_fit +
    values.scene_consistency +
    values.grammar_punctuation
  )
}

export function calculateScenePreviewTotal(values: {
  voice_consistency: number
  terminology_consistency: number
  emotional_progression: number
  relationship_continuity: number
  narrative_coherence: number
  genre_tone_consistency: number
}): number {
  return (
    values.voice_consistency +
    values.terminology_consistency +
    values.emotional_progression +
    values.relationship_continuity +
    values.narrative_coherence +
    values.genre_tone_consistency
  )
}

export function formatCoveragePercentage(value: number): string {
  return `${value.toFixed(1)}%`
}

export function formatHardFailureRatePercentage(
  value: number | null | undefined,
  decimals = 1
): string {
  if (value === null || value === undefined) return "—"
  return `${(value * 100).toFixed(decimals)}%`
}

export function formatNullableMetric(
  value: number | null | undefined,
  decimals = 2
): string {
  if (value === null || value === undefined) return "—"
  return value.toFixed(decimals)
}

export function isPartialExplicitSelection(params: {
  plain_run_id: number | null
  context_run_id: number | null
  context_memory_run_id: number | null
}): boolean {
  const values = [params.plain_run_id, params.context_run_id, params.context_memory_run_id]
  const someSet = values.some((v) => v !== null)
  const allSet = values.every((v) => v !== null)
  return someSet && !allSet
}

export function hasDuplicateIds(
  ids: (number | null)[]
): boolean {
  const defined = ids.filter((id) => id !== null) as number[]
  return new Set(defined).size !== defined.length
}
