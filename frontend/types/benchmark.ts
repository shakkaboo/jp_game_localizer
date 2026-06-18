export interface BenchmarkDatasetListItem {
  id: number
  name: string
  version: string
  source_or_author: string
  review_status: string
  created_at: string
  scene_count: number
  item_count: number
}

export interface BenchmarkItemRead {
  id: number
  scene_id: number
  sequence_number: number
  source_text_ja: string
  reference_en: string
  speaker: string | null
  character_voice_context: string | null
  relationship_context: string | null
  glossary_expectations: string | null
  placeholder_expectations: string | null
  requires_previous_memory: boolean
  created_at: string
}

export interface BenchmarkSceneRead {
  id: number
  dataset_id: number
  scene_number: number
  title: string | null
  genre: string
  content_type: string
  setting_or_location: string | null
  tone: string | null
  context_json: string | null
  notes: string | null
  created_at: string
  items: BenchmarkItemRead[]
}

export interface BenchmarkDatasetRead {
  id: number
  name: string
  version: string
  source_or_author: string
  license_or_usage_status: string
  reference_translation_method: string
  review_status: string
  description: string | null
  created_at: string
  scenes: BenchmarkSceneRead[]
}

export interface BenchmarkRunRead {
  id: number
  dataset_id: number
  mode: string
  llm_provider: string
  llm_model: string
  prompt_version: string
  status: string
  created_at: string
  completed_at: string | null
  error_message: string | null
  memory_gap: boolean
  total_scenes: number
  completed_scenes: number
  notes: string | null
}

export interface BenchmarkRunStartResponse {
  run_id: number
  dataset_id: number
  mode: string
  status: string
  total_scenes: number
  completed_scenes: number
  memory_gap: boolean
}

export interface BenchmarkAutomaticScoreRead {
  id: number
  benchmark_output_id: number
  chrf_score: number | null
  bleu_score: number | null
  glossary_compliant: boolean | null
  placeholders_preserved: boolean | null
  missing_output: boolean
  untranslated_japanese: boolean | null
  line_id_mismatch: boolean
  speaker_mismatch: boolean | null
  details_json: string | null
  created_at: string
}

export interface BenchmarkOutputRead {
  id: number
  run_id: number
  benchmark_item_id: number
  scene_id: number
  sequence_number: number
  output_localized_text_en: string | null
  output_literal_meaning: string | null
  output_localization_note: string | null
  status: string
  error_message: string | null
  score: BenchmarkAutomaticScoreRead | null
}

export interface BenchmarkOutputWithItemRead {
  output: BenchmarkOutputRead
  item: BenchmarkItemRead | null
  scene: BenchmarkSceneRead
}

export interface BenchmarkRunSceneOutput {
  scene: BenchmarkSceneRead
  outputs: BenchmarkOutputWithItemRead[]
}

export interface BenchmarkRunDetailRead extends BenchmarkRunRead {
  scenes: BenchmarkRunSceneOutput[]
}

export interface BenchmarkMetricsPerCategory {
  count: number
  mean_chrf: number | null
  std_chrf: number | null
}

export interface BenchmarkMetricsSummary {
  dataset_name: string
  dataset_version: string
  mode: string
  model: string
  provider: string
  prompt_version: string
  status: string
  total_items: number
  completed_items: number
  failed_items: number
  chrf: Record<string, number> | null
  bleu: Record<string, number> | null
  glossary_compliance_rate: number | null
  placeholder_preservation_rate: number | null
  missing_output_count: number
  untranslated_japanese_count: number
  line_id_mismatch_count: number
  speaker_mismatch_count: number
  memory_gap: boolean
  per_genre: Record<string, BenchmarkMetricsPerCategory>
  per_content_type: Record<string, BenchmarkMetricsPerCategory>
  per_scene: Record<string, BenchmarkMetricsPerCategory>
  requires_previous_memory: BenchmarkMetricsPerCategory | null
  no_previous_memory: BenchmarkMetricsPerCategory | null
}

export type RunMode = "plain" | "context" | "context_memory"

export type RunStatus =
  | "pending"
  | "running"
  | "completed"
  | "completed_with_errors"
  | "failed"

export type OutputStatus =
  | "completed"
  | "failed"
  | "missing"
