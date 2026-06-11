export interface ContextUploadResponse {
  project_id: number
  file_type: string
  project: {
    title: string
    genre?: string
    target_tone?: string
  } | null
  sections: string[]
  warnings: string[]
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
  project_id: number
  chunks: ChunkItem[]
}

export interface ChunkItem {
  id: number
  project_id: number
  source_file_id: number
  chunk_number: number
  chunk_title: string
  scene_hint: string
  status: string
  lines_count?: number
  previous_memory?: string | null
}

export interface ChunkDetail {
  id: number
  project_id: number
  source_file_id: number
  chunk_number: number
  chunk_title: string
  scene_hint: string
  status: string
  previous_memory_json: string | null
  chunk_memory_json: string | null
  source_lines: SourceLine[]
  translations: TranslationDetail[]
}

export interface SourceLine {
  id: number
  line_id: string
  character: string
  source_text_ja: string
  scene_hint: string | null
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
  detail: string
}
