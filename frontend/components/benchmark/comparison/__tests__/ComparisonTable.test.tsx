import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import ComparisonTable from "@/components/benchmark/comparison/ComparisonTable"
import type { BenchmarkCompareEntry } from "@/types/benchmark"

const baseEntry: BenchmarkCompareEntry = {
  run_id: 1,
  mode: "plain",
  status: "completed",
  model: "gpt-4",
  provider: "openai",
  prompt_version: "v1",
  memory_gap: false,
  automatic_metrics: {
    dataset_name: "Test",
    dataset_version: "1",
    mode: "plain",
    model: "gpt-4",
    provider: "openai",
    prompt_version: "v1",
    status: "completed",
    total_items: 10,
    completed_items: 10,
    failed_items: 0,
    chrf: { mean: 75.0 },
    bleu: null,
    glossary_compliance_rate: 0.9,
    placeholder_preservation_rate: 1.0,
    missing_output_count: 0,
    untranslated_japanese_count: 0,
    line_id_mismatch_count: 1,
    speaker_mismatch_count: 0,
    memory_gap: false,
    per_genre: {},
    per_content_type: {},
    per_scene: {},
    requires_previous_memory: null,
    no_previous_memory: null,
  },
  human_metrics: {
    run_id: 1,
    mode: "plain",
    model: "gpt-4",
    provider: "openai",
    prompt_version: "v1",
    item_review_coverage_percentage: 0.8,
    scene_review_coverage_percentage: 0.5,
    hard_failure_review_coverage_percentage: 0.6,
    item_scores: {
      item_evaluation_count: 8,
      unique_reviewed_output_count: 8,
      average_reviewers_per_reviewed_output: 1.0,
      average_total: 85.5,
      average_per_criterion: {},
      by_scene: {},
      by_genre: {},
      by_content_type: {},
      requires_previous_memory: null,
      no_previous_memory: null,
      by_reviewer: {},
    },
    scene_scores: {
      scene_evaluation_count: 3,
      unique_reviewed_scenes: 3,
      scene_review_coverage_percentage: 0.5,
      average_total: 80.0,
      average_per_criterion: {},
      by_reviewer: {},
    },
    hard_failures: {
      hard_failure_review_count: 6,
      unique_outputs_reviewed_for_hard_failures: 6,
      outputs_with_any_hard_failure: 2,
      hard_failure_rate_among_reviewed_outputs: 33.3,
      count_per_flag: { wrong_speaker: 1, missing_critical_meaning: 1 },
      by_scene: {},
      by_genre: {},
      by_content_type: {},
      requires_previous_memory: 0,
      no_previous_memory: 2,
      by_reviewer: {},
    },
  },
  item_review_coverage_percentage: 0.8,
  scene_review_coverage_percentage: 0.5,
  hard_failure_review_coverage_percentage: 0.6,
  coverage_note: null,
}

const entries: BenchmarkCompareEntry[] = [
  { ...baseEntry, run_id: 1, mode: "plain" },
  { ...baseEntry, run_id: 2, mode: "context" },
  { ...baseEntry, run_id: 3, mode: "context_memory" },
]

describe("ComparisonTable", () => {
  it("renders three columns for three modes", () => {
    render(<ComparisonTable entries={entries} />)
    expect(screen.getAllByText("Plain").length).toBeGreaterThanOrEqual(3)
    expect(screen.getAllByText("Context").length).toBeGreaterThanOrEqual(3)
    expect(screen.getAllByText("Context + Memory").length).toBeGreaterThanOrEqual(3)
  })

  it("renders section headers", () => {
    render(<ComparisonTable entries={entries} />)
    expect(screen.getByText("Run Metadata")).toBeInTheDocument()
    expect(screen.getByText("Automatic Metrics")).toBeInTheDocument()
    expect(screen.getByText("Human Item Metrics")).toBeInTheDocument()
    expect(screen.getByText("Human Scene Metrics")).toBeInTheDocument()
    expect(screen.getByText("Hard-Failure Metrics")).toBeInTheDocument()
  })

  it("renders automatic metrics values", () => {
    render(<ComparisonTable entries={entries} />)
    expect(screen.getAllByText("chrF").length).toBeGreaterThanOrEqual(3)
  })

  it("renders null as em dash", () => {
    const nullEntry: BenchmarkCompareEntry = {
      ...baseEntry,
      run_id: 1,
      mode: "plain",
      automatic_metrics: {
        ...baseEntry.automatic_metrics!,
        chrf: null,
        bleu: null,
      },
    }
    render(<ComparisonTable entries={[nullEntry]} />)
    // Should not crash with null values
  })
})

describe("ComparisonTable with no human data", () => {
  it('shows "No human item-review data" when human_metrics is null', () => {
    const noHumanEntry: BenchmarkCompareEntry[] = [
      {
        ...baseEntry,
        human_metrics: null,
        item_review_coverage_percentage: 0,
        scene_review_coverage_percentage: 0,
        hard_failure_review_coverage_percentage: 0,
      },
    ]
    render(<ComparisonTable entries={noHumanEntry} />)
    const noDataElements = screen.getAllByText("No human item-review data")
    // Human Item Metrics section shows it
    // Human Scene Metrics section shows it
    // Hard-Failure Metrics section shows it
    expect(noDataElements.length).toBeGreaterThanOrEqual(3)
  })
})

describe("ComparisonTable with memory gap warning", () => {
  it("shows memory gap indicator", () => {
    const gapEntry: BenchmarkCompareEntry[] = [
      {
        ...baseEntry,
        memory_gap: true,
      },
    ]
    render(<ComparisonTable entries={gapEntry} />)
    expect(screen.getByText("Yes")).toBeInTheDocument()
  })
})
