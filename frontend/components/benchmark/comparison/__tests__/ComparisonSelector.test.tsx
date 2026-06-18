import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import ComparisonSelector from "@/components/benchmark/comparison/ComparisonSelector"
import type { BenchmarkRunRead } from "@/types/benchmark"

const mockDatasets = [
  { id: 1, name: "Test Dataset", version: "1.0" },
]

const mockRuns: BenchmarkRunRead[] = [
  { id: 1, dataset_id: 1, mode: "plain", llm_provider: "openai", llm_model: "gpt-4", prompt_version: "v1", status: "completed", created_at: "2025-01-01T00:00:00Z", completed_at: "2025-01-01T01:00:00Z", error_message: null, memory_gap: false, total_scenes: 5, completed_scenes: 5, notes: null },
  { id: 2, dataset_id: 1, mode: "context", llm_provider: "openai", llm_model: "gpt-4", prompt_version: "v1", status: "completed", created_at: "2025-01-01T00:00:00Z", completed_at: "2025-01-01T01:00:00Z", error_message: null, memory_gap: false, total_scenes: 5, completed_scenes: 5, notes: null },
  { id: 3, dataset_id: 1, mode: "context_memory", llm_provider: "openai", llm_model: "gpt-4", prompt_version: "v1", status: "completed", created_at: "2025-01-01T00:00:00Z", completed_at: "2025-01-01T01:00:00Z", error_message: null, memory_gap: false, total_scenes: 5, completed_scenes: 5, notes: null },
  { id: 4, dataset_id: 1, mode: "plain", llm_provider: "openai", llm_model: "gpt-4", prompt_version: "v1", status: "pending", created_at: "2025-01-01T00:00:00Z", completed_at: null, error_message: null, memory_gap: false, total_scenes: 5, completed_scenes: 0, notes: null },
]

describe("ComparisonSelector", () => {
  const defaultProps = {
    datasets: mockDatasets,
    runs: mockRuns,
    mode: "explicit" as const,
    onModeChange: vi.fn(),
    selectedDatasetId: null as number | null,
    onDatasetChange: vi.fn(),
    plainRunId: null as number | null,
    contextRunId: null as number | null,
    contextMemoryRunId: null as number | null,
    onPlainRunChange: vi.fn(),
    onContextRunChange: vi.fn(),
    onContextMemoryRunChange: vi.fn(),
    onCompare: vi.fn(),
    loading: false,
  }

  it("renders mode toggle buttons", () => {
    render(<ComparisonSelector {...defaultProps} />)
    expect(screen.getByText("Select Explicit Runs")).toBeInTheDocument()
    expect(screen.getByText("Latest Completed per Mode")).toBeInTheDocument()
  })

  it("shows run selects in explicit mode", () => {
    render(<ComparisonSelector {...defaultProps} />)
    expect(screen.getByText("Plain")).toBeInTheDocument()
    expect(screen.getByText("Context")).toBeInTheDocument()
    expect(screen.getByText("Context + Memory")).toBeInTheDocument()
  })

  it("disables compare button when no runs selected in explicit mode", () => {
    render(<ComparisonSelector {...defaultProps} />)
    expect(screen.getByText("Compare Modes")).toBeDisabled()
  })

  it("enables compare button when all three explicit runs selected", () => {
    render(
      <ComparisonSelector
        {...defaultProps}
        selectedDatasetId={1}
        plainRunId={1}
        contextRunId={2}
        contextMemoryRunId={3}
      />
    )
    expect(screen.getByText("Compare Modes")).not.toBeDisabled()
  })

  it("prevents selecting the same run for multiple modes when all three selected", () => {
    render(
      <ComparisonSelector
        {...defaultProps}
        selectedDatasetId={1}
        plainRunId={1}
        contextRunId={2}
        contextMemoryRunId={3}
      />
    )
    const plainSelect = screen.getByLabelText("Plain") as HTMLSelectElement
    const plainOptions = Array.from(plainSelect.options).map((o) => o.value)
    expect(plainOptions).not.toContain("2")
    expect(plainOptions).not.toContain("3")
  })

  it("shows latest-mode description when mode is latest", () => {
    render(<ComparisonSelector {...defaultProps} mode="latest" />)
    expect(
      screen.getByText(/backend selects the latest completed/)
    ).toBeInTheDocument()
  })

  it("disables compare when no dataset selected in latest mode", () => {
    render(<ComparisonSelector {...defaultProps} mode="latest" />)
    expect(screen.getByText("Compare Modes")).toBeDisabled()
  })

  it("enables compare when dataset selected in latest mode", () => {
    render(
      <ComparisonSelector {...defaultProps} mode="latest" selectedDatasetId={1} />
    )
    expect(screen.getByText("Compare Modes")).not.toBeDisabled()
  })

  it("calls onCompare when compare button clicked", () => {
    const onCompare = vi.fn()
    render(
      <ComparisonSelector
        {...defaultProps}
        selectedDatasetId={1}
        plainRunId={1}
        contextRunId={2}
        contextMemoryRunId={3}
        onCompare={onCompare}
      />
    )
    fireEvent.click(screen.getByText("Compare Modes"))
    expect(onCompare).toHaveBeenCalledTimes(1)
  })

  it("filters out pending runs from selector options", () => {
    render(
      <ComparisonSelector
        {...defaultProps}
        selectedDatasetId={1}
      />
    )
    const plainSelect = screen.getByLabelText("Plain") as HTMLSelectElement
    expect(plainSelect.querySelector('option[value="4"]')).toBeNull()
  })
})
