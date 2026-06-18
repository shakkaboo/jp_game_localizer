import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import ReviewCoverageCard from "@/components/benchmark/review/ReviewCoverageCard"

describe("ReviewCoverageCard", () => {
  it("renders label and value", () => {
    render(<ReviewCoverageCard label="Tests" value={42} />)
    expect(screen.getByText("Tests")).toBeInTheDocument()
    expect(screen.getByText("42")).toBeInTheDocument()
  })

  it("renders suffix when provided", () => {
    render(<ReviewCoverageCard label="Score" value={85} suffix="/ 100" />)
    expect(screen.getByText("/ 100")).toBeInTheDocument()
  })

  it("renders subtext when provided", () => {
    render(<ReviewCoverageCard label="Coverage" value="80%" subtext="Based on 10 items" />)
    expect(screen.getByText("Based on 10 items")).toBeInTheDocument()
  })

  it("renders em dash for null value", () => {
    render(<ReviewCoverageCard label="Empty" value={null} />)
    expect(screen.getByText("—")).toBeInTheDocument()
  })

  it("renders em dash for undefined value", () => {
    render(<ReviewCoverageCard label="Empty" value={undefined} />)
    expect(screen.getByText("—")).toBeInTheDocument()
  })

  it("renders zero correctly", () => {
    render(<ReviewCoverageCard label="Count" value={0} />)
    expect(screen.getByText("0")).toBeInTheDocument()
  })
})
