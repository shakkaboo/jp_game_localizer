import { describe, it, expect } from "vitest"
import {
  normalizeReviewerLabel,
  calculateItemPreviewTotal,
  calculateScenePreviewTotal,
  formatNullableMetric,
  isPartialExplicitSelection,
  hasDuplicateIds,
} from "../benchmark-helpers"

describe("normalizeReviewerLabel", () => {
  it("trims leading and trailing whitespace", () => {
    expect(normalizeReviewerLabel("  hello  ")).toBe("hello")
  })

  it("collapses repeated internal whitespace", () => {
    expect(normalizeReviewerLabel("hello   world")).toBe("hello world")
  })

  it("preserves case", () => {
    expect(normalizeReviewerLabel("  RevIeWer-1  ")).toBe("RevIeWer-1")
  })

  it("returns empty string for whitespace-only input", () => {
    expect(normalizeReviewerLabel("   ")).toBe("")
  })
})

describe("calculateItemPreviewTotal", () => {
  it("sums all 8 criteria correctly", () => {
    const result = calculateItemPreviewTotal({
      meaning_preservation: 25,
      omission_addition_control: 15,
      natural_english: 15,
      character_voice: 15,
      glossary_consistency: 10,
      genre_tone_fit: 10,
      scene_consistency: 5,
      grammar_punctuation: 5,
    })
    expect(result).toBe(100)
  })

  it("returns 0 for all zeros", () => {
    const result = calculateItemPreviewTotal({
      meaning_preservation: 0,
      omission_addition_control: 0,
      natural_english: 0,
      character_voice: 0,
      glossary_consistency: 0,
      genre_tone_fit: 0,
      scene_consistency: 0,
      grammar_punctuation: 0,
    })
    expect(result).toBe(0)
  })
})

describe("calculateScenePreviewTotal", () => {
  it("sums all 6 criteria correctly", () => {
    const result = calculateScenePreviewTotal({
      voice_consistency: 25,
      terminology_consistency: 20,
      emotional_progression: 15,
      relationship_continuity: 15,
      narrative_coherence: 15,
      genre_tone_consistency: 10,
    })
    expect(result).toBe(100)
  })
})

describe("formatNullableMetric", () => {
  it("returns em dash for null", () => {
    expect(formatNullableMetric(null)).toBe("—")
  })

  it("returns em dash for undefined", () => {
    expect(formatNullableMetric(undefined)).toBe("—")
  })

  it("formats number to 2 decimals by default", () => {
    expect(formatNullableMetric(3.14159)).toBe("3.14")
  })

  it("formats number to specified decimals", () => {
    expect(formatNullableMetric(0.5, 1)).toBe("0.5")
  })
})

describe("isPartialExplicitSelection", () => {
  it("returns false when all three are null", () => {
    expect(isPartialExplicitSelection({
      plain_run_id: null,
      context_run_id: null,
      context_memory_run_id: null,
    })).toBe(false)
  })

  it("returns false when all three are set", () => {
    expect(isPartialExplicitSelection({
      plain_run_id: 1,
      context_run_id: 2,
      context_memory_run_id: 3,
    })).toBe(false)
  })

  it("returns true when only one is set", () => {
    expect(isPartialExplicitSelection({
      plain_run_id: 1,
      context_run_id: null,
      context_memory_run_id: null,
    })).toBe(true)
  })

  it("returns true when only two are set", () => {
    expect(isPartialExplicitSelection({
      plain_run_id: 1,
      context_run_id: 2,
      context_memory_run_id: null,
    })).toBe(true)
  })
})

describe("hasDuplicateIds", () => {
  it("returns false for all unique", () => {
    expect(hasDuplicateIds([1, 2, 3])).toBe(false)
  })

  it("returns true for duplicates", () => {
    expect(hasDuplicateIds([1, 2, 1])).toBe(true)
  })

  it("ignores nulls", () => {
    expect(hasDuplicateIds([1, null, 1])).toBe(true)
  })
})
