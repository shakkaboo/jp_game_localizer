export interface ContextUploadResponse {
  project_id: number
  file_type: string
  project: {
    title?: string
    genre?: string
    target_tone?: string
  } | Record<string, unknown>
  characters_count: number
  relationships_count: number
  glossary_count: number
  style_rules_count: number
  warnings: string[]
  sections?: string[]
}

export interface ScriptUploadResponse {
  project_id: number
  source_file_id: number
  file_type: string
  total_lines: number
  detected_characters: string[]
  detected_scene_hints: string[]
  warnings: string[]
}

export interface ChunkCreateResponse {
  message?: string
  project_id: number
  chunks: ChunkItem[]
}

export interface ChunkItem {
  id: number
  project_id?: number
  source_file_id: number
  chunk_number: number
  chunk_title: string
  scene_hint: string
  status: string
  lines_count?: number
  previous_memory_json?: Record<string, unknown> | string | null
  chunk_memory_json?: Record<string, unknown> | string | null
}

export interface ChunkDetail {
  id: number
  project_id: number
  source_file_id: number
  chunk_number: number
  chunk_title: string
  scene_hint: string
  status: string
  previous_memory_json: Record<string, unknown> | string | null
  chunk_memory_json: Record<string, unknown> | string | null
  source_lines: SourceLine[]
  translations: TranslationDetail[]
}

export interface SourceLine {
  id: number
  project_id?: number
  source_file_id?: number
  line_id: string
  character: string
  source_text_ja: string
  scene_hint: string | null
  chunk_id?: number
}

export interface TranslationDetail {
  id: number
  project_id: number
  chunk_id: number
  source_line_id: number
  literal_meaning: string
  localized_text_en: string
  final_text_en: string
  localization_note: string
  status: string
}

export interface TranslateResponse {
  chunk_id: number
  status: string
  translations_count: number
  chunk_memory: Record<string, unknown>
  warnings: string[]
}

export interface ExportItem {
  line_id: string
  character: string
  source_text_ja: string
  localized_text_en: string
  final_text_en: string
  chunk_number: number
  chunk_title: string
  status: string
}

export interface ApiError {
  detail: string | { msg?: string; type?: string; loc?: unknown[] }[]
}