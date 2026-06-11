import type {
  ContextUploadResponse,
  ScriptUploadResponse,
  ChunkCreateResponse,
  ChunkItem,
  ChunkDetail,
  TranslateResponse,
  ExportItem,
} from "@/types"

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    ...options,
    headers: {
      ...(options?.headers || {}),
    },
  })
  if (!res.ok) {
    let detail = `Request failed: ${res.status}`
    try {
      const body = await res.json()
      if (body.detail) detail = body.detail
    } catch {
      // ignore parse error
    }
    throw new Error(detail)
  }
  return res.json()
}

function formDataRequest<T>(url: string, file: File): Promise<T> {
  const fd = new FormData()
  fd.append("file", file)
  return request<T>(url, { method: "POST", body: fd })
}

export async function uploadContext(file: File) {
  return formDataRequest<ContextUploadResponse>("/upload/context", file)
}

export async function uploadScript(projectId: number, file: File) {
  return formDataRequest<ScriptUploadResponse>(
    `/upload/script/${projectId}`,
    file
  )
}

export async function createChunks(projectId: number) {
  return request<ChunkCreateResponse>(`/chunks/create/${projectId}`, {
    method: "POST",
  })
}

export async function listChunks(projectId: number) {
  return request<ChunkItem[]>(`/chunks/${projectId}`)
}

export async function getChunkDetail(chunkId: number) {
  return request<ChunkDetail>(`/chunks/detail/${chunkId}`)
}

export async function translateChunk(chunkId: number) {
  return request<TranslateResponse>(`/translate/chunk/${chunkId}`, {
    method: "POST",
  })
}

export async function patchTranslation(
  translationId: number,
  body: Record<string, string>
) {
  return request<unknown>(`/translate/${translationId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
}

export function getExportUrl(projectId: number, format: "csv" | "json") {
  return `${BASE}/export/${projectId}?format=${format}`
}

export async function fetchExportData(
  projectId: number,
  format: "csv" | "json"
) {
  if (format === "json") {
    return request<ExportItem[]>(`/export/${projectId}?format=json`)
  }
  const res = await fetch(`${BASE}/export/${projectId}?format=csv`)
  return res.text()
}
