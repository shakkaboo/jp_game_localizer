import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { compareExplicitRuns, compareLatestCompleted } from "../benchmark-api"

function mockFetchResponse(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response
}

describe("compareExplicitRuns", () => {
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch").mockImplementation(
      () => Promise.resolve(mockFetchResponse(200, {}))
    )
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("constructs correct query params", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch")

    await compareExplicitRuns(1, 2, 3)

    const url = fetchSpy.mock.calls[0][0] as string
    expect(url).toContain("/benchmark/compare")
    expect(url).toContain("plain_run_id=1")
    expect(url).toContain("context_run_id=2")
    expect(url).toContain("context_memory_run_id=3")
  })

  it("throws on non-ok response", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(
      () => Promise.resolve(mockFetchResponse(400, { detail: "Bad request" }))
    )

    await expect(compareExplicitRuns(1, 2, 3)).rejects.toThrow("Bad request")
  })
})

describe("compareLatestCompleted", () => {
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch").mockImplementation(
      () => Promise.resolve(mockFetchResponse(200, {}))
    )
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("constructs correct query params", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch")

    await compareLatestCompleted(5)

    const url = fetchSpy.mock.calls[0][0] as string
    expect(url).toContain("/benchmark/compare")
    expect(url).toContain("dataset_id=5")
    expect(url).toContain("selection=latest_completed")
  })

  it("throws on error response", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(
      () => Promise.resolve(mockFetchResponse(404, { detail: "Dataset not found" }))
    )

    await expect(compareLatestCompleted(999)).rejects.toThrow("Dataset not found")
  })
})
