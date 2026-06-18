import type {
  BenchmarkDatasetListItem,
  BenchmarkDatasetRead,
  BenchmarkHardFailureCreate,
  BenchmarkHardFailureRead,
  BenchmarkHardFailureUpdate,
  BenchmarkHumanMetricsSummary,
  BenchmarkItemEvaluationCreate,
  BenchmarkItemEvaluationRead,
  BenchmarkItemEvaluationUpdate,
  BenchmarkMetricsSummary,
  BenchmarkOutputWithItemRead,
  BenchmarkRunDetailRead,
  BenchmarkRunRead,
  BenchmarkRunSceneOutput,
  BenchmarkRunStartResponse,
  BenchmarkSceneEvaluationCreate,
  BenchmarkSceneEvaluationRead,
  BenchmarkSceneEvaluationUpdate,
} from "@/types/benchmark"

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  })
  if (!res.ok) {
    let detail = `Request failed: ${res.status}`
    try {
      const body = await res.json()
      if (body.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)
      }
    } catch {
      // ignore parse error
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function listDatasets(): Promise<BenchmarkDatasetListItem[]> {
  return request<BenchmarkDatasetListItem[]>("/benchmark/datasets")
}

export async function getDataset(datasetId: number): Promise<BenchmarkDatasetRead> {
  return request<BenchmarkDatasetRead>(`/benchmark/datasets/${datasetId}`)
}

export async function startRun(
  datasetId: number,
  mode: string
): Promise<BenchmarkRunStartResponse> {
  return request<BenchmarkRunStartResponse>("/benchmark/runs", {
    method: "POST",
    body: JSON.stringify({ dataset_id: datasetId, mode }),
  })
}

export async function listRuns(
  datasetId?: number,
  mode?: string
): Promise<BenchmarkRunRead[]> {
  const params = new URLSearchParams()
  if (datasetId !== undefined) params.set("dataset_id", String(datasetId))
  if (mode !== undefined) params.set("mode", mode)
  const qs = params.toString()
  return request<BenchmarkRunRead[]>(`/benchmark/runs${qs ? `?${qs}` : ""}`)
}

export async function getRun(runId: number): Promise<BenchmarkRunDetailRead> {
  return request<BenchmarkRunDetailRead>(`/benchmark/runs/${runId}`)
}

export async function getRunScene(
  runId: number,
  sceneNumber: number
): Promise<BenchmarkRunSceneOutput> {
  return request<BenchmarkRunSceneOutput>(
    `/benchmark/runs/${runId}/scenes/${sceneNumber}`
  )
}

export async function getRunItem(
  runId: number,
  benchmarkItemId: number
): Promise<BenchmarkOutputWithItemRead> {
  return request<BenchmarkOutputWithItemRead>(
    `/benchmark/runs/${runId}/items/${benchmarkItemId}`
  )
}

export async function getRunMetrics(
  runId: number
): Promise<BenchmarkMetricsSummary> {
  return request<BenchmarkMetricsSummary>(`/benchmark/runs/${runId}/metrics`)
}

export async function createItemEvaluation(
  runId: number,
  body: BenchmarkItemEvaluationCreate
): Promise<BenchmarkItemEvaluationRead> {
  return request<BenchmarkItemEvaluationRead>(
    `/benchmark/runs/${runId}/evaluations/items`,
    { method: "POST", body: JSON.stringify(body) }
  )
}

export async function updateItemEvaluation(
  evaluationId: number,
  body: BenchmarkItemEvaluationUpdate
): Promise<BenchmarkItemEvaluationRead> {
  return request<BenchmarkItemEvaluationRead>(
    `/benchmark/evaluations/items/${evaluationId}`,
    { method: "PUT", body: JSON.stringify(body) }
  )
}

export async function getItemEvaluation(
  evaluationId: number
): Promise<BenchmarkItemEvaluationRead> {
  return request<BenchmarkItemEvaluationRead>(
    `/benchmark/evaluations/items/${evaluationId}`
  )
}

export async function listItemEvaluations(
  runId: number,
  outputId?: number
): Promise<BenchmarkItemEvaluationRead[]> {
  const params = new URLSearchParams()
  if (outputId !== undefined) params.set("benchmark_output_id", String(outputId))
  const qs = params.toString()
  return request<BenchmarkItemEvaluationRead[]>(
    `/benchmark/runs/${runId}/evaluations/items${qs ? `?${qs}` : ""}`
  )
}

export async function createSceneEvaluation(
  runId: number,
  body: BenchmarkSceneEvaluationCreate
): Promise<BenchmarkSceneEvaluationRead> {
  return request<BenchmarkSceneEvaluationRead>(
    `/benchmark/runs/${runId}/evaluations/scenes`,
    { method: "POST", body: JSON.stringify(body) }
  )
}

export async function updateSceneEvaluation(
  evaluationId: number,
  body: BenchmarkSceneEvaluationUpdate
): Promise<BenchmarkSceneEvaluationRead> {
  return request<BenchmarkSceneEvaluationRead>(
    `/benchmark/evaluations/scenes/${evaluationId}`,
    { method: "PUT", body: JSON.stringify(body) }
  )
}

export async function getSceneEvaluation(
  evaluationId: number
): Promise<BenchmarkSceneEvaluationRead> {
  return request<BenchmarkSceneEvaluationRead>(
    `/benchmark/evaluations/scenes/${evaluationId}`
  )
}

export async function listSceneEvaluations(
  runId: number
): Promise<BenchmarkSceneEvaluationRead[]> {
  return request<BenchmarkSceneEvaluationRead[]>(
    `/benchmark/runs/${runId}/evaluations/scenes`
  )
}

export async function createHardFailure(
  runId: number,
  body: BenchmarkHardFailureCreate
): Promise<BenchmarkHardFailureRead> {
  return request<BenchmarkHardFailureRead>(
    `/benchmark/runs/${runId}/hard-failures`,
    { method: "POST", body: JSON.stringify(body) }
  )
}

export async function updateHardFailure(
  failureId: number,
  body: BenchmarkHardFailureUpdate
): Promise<BenchmarkHardFailureRead> {
  return request<BenchmarkHardFailureRead>(
    `/benchmark/hard-failures/${failureId}`,
    { method: "PUT", body: JSON.stringify(body) }
  )
}

export async function getHardFailure(
  failureId: number
): Promise<BenchmarkHardFailureRead> {
  return request<BenchmarkHardFailureRead>(
    `/benchmark/hard-failures/${failureId}`
  )
}

export async function listHardFailures(
  runId: number,
  outputId?: number
): Promise<BenchmarkHardFailureRead[]> {
  const params = new URLSearchParams()
  if (outputId !== undefined) params.set("benchmark_output_id", String(outputId))
  const qs = params.toString()
  return request<BenchmarkHardFailureRead[]>(
    `/benchmark/runs/${runId}/hard-failures${qs ? `?${qs}` : ""}`
  )
}

export async function getHumanMetrics(
  runId: number
): Promise<BenchmarkHumanMetricsSummary> {
  return request<BenchmarkHumanMetricsSummary>(
    `/benchmark/runs/${runId}/human-metrics`
  )
}
