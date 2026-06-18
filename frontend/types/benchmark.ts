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

export interface BenchmarkItemEvaluationCreate {
  benchmark_output_id: number
  reviewer_label: string
  meaning_preservation: number
  omission_addition_control: number
  natural_english: number
  character_voice: number
  glossary_consistency: number
  genre_tone_fit: number
  scene_consistency: number
  grammar_punctuation: number
  reviewer_notes: string | null
}

export interface BenchmarkItemEvaluationUpdate {
  meaning_preservation: number
  omission_addition_control: number
  natural_english: number
  character_voice: number
  glossary_consistency: number
  genre_tone_fit: number
  scene_consistency: number
  grammar_punctuation: number
  reviewer_notes: string | null
}

export interface BenchmarkItemEvaluationRead {
  id: number
  benchmark_output_id: number
  reviewer_label: string
  meaning_preservation: number
  omission_addition_control: number
  natural_english: number
  character_voice: number
  glossary_consistency: number
  genre_tone_fit: number
  scene_consistency: number
  grammar_punctuation: number
  total_score: number
  reviewer_notes: string | null
  created_at: string
  updated_at: string
}

export interface BenchmarkSceneEvaluationCreate {
  scene_id: number
  reviewer_label: string
  voice_consistency: number
  terminology_consistency: number
  emotional_progression: number
  relationship_continuity: number
  narrative_coherence: number
  genre_tone_consistency: number
  reviewer_notes: string | null
}

export interface BenchmarkSceneEvaluationUpdate {
  voice_consistency: number
  terminology_consistency: number
  emotional_progression: number
  relationship_continuity: number
  narrative_coherence: number
  genre_tone_consistency: number
  reviewer_notes: string | null
}

export interface BenchmarkSceneEvaluationRead {
  id: number
  run_id: number
  scene_id: number
  reviewer_label: string
  voice_consistency: number
  terminology_consistency: number
  emotional_progression: number
  relationship_continuity: number
  narrative_coherence: number
  genre_tone_consistency: number
  total_score: number
  reviewer_notes: string | null
  created_at: string
  updated_at: string
}

export interface BenchmarkHardFailureCreate {
  benchmark_output_id: number
  reviewer_label: string
  invented_plot_information: boolean
  missing_critical_meaning: boolean
  wrong_speaker: boolean
  broken_placeholder: boolean
  major_glossary_violation: boolean
  contradiction_with_previous_scene: boolean
  unjustified_untranslated_japanese: boolean
  explanation: string | null
}

export interface BenchmarkHardFailureUpdate {
  invented_plot_information: boolean
  missing_critical_meaning: boolean
  wrong_speaker: boolean
  broken_placeholder: boolean
  major_glossary_violation: boolean
  contradiction_with_previous_scene: boolean
  unjustified_untranslated_japanese: boolean
  explanation: string | null
}

export interface BenchmarkHardFailureRead {
  id: number
  benchmark_output_id: number
  reviewer_label: string
  invented_plot_information: boolean
  missing_critical_meaning: boolean
  wrong_speaker: boolean
  broken_placeholder: boolean
  major_glossary_violation: boolean
  contradiction_with_previous_scene: boolean
  unjustified_untranslated_japanese: boolean
  explanation: string | null
  created_at: string
  updated_at: string
}

export interface BenchmarkCriterionStats {
  mean: number | null
  std: number | null
}

export interface BenchmarkHumanItemScoreAggregate {
  item_evaluation_count: number
  unique_reviewed_output_count: number
  average_reviewers_per_reviewed_output: number
  average_total: number | null
  average_per_criterion: Record<string, BenchmarkCriterionStats | null>
  by_scene: Record<string, Record<string, unknown> | null>
  by_genre: Record<string, Record<string, unknown> | null>
  by_content_type: Record<string, Record<string, unknown> | null>
  requires_previous_memory: Record<string, unknown> | null
  no_previous_memory: Record<string, unknown> | null
  by_reviewer: Record<string, Record<string, unknown> | null>
}

export interface BenchmarkHumanSceneScoreAggregate {
  scene_evaluation_count: number
  unique_reviewed_scenes: number
  scene_review_coverage_percentage: number
  average_total: number | null
  average_per_criterion: Record<string, BenchmarkCriterionStats | null>
  by_reviewer: Record<string, Record<string, unknown> | null>
}

export interface BenchmarkHardFailureAggregate {
  hard_failure_review_count: number
  unique_outputs_reviewed_for_hard_failures: number
  outputs_with_any_hard_failure: number
  hard_failure_rate_among_reviewed_outputs: number | null
  count_per_flag: Record<string, number>
  by_scene: Record<string, number>
  by_genre: Record<string, number>
  by_content_type: Record<string, number>
  requires_previous_memory: number
  no_previous_memory: number
  by_reviewer: Record<string, number>
}

export interface BenchmarkHumanMetricsSummary {
  run_id: number
  mode: string
  model: string
  provider: string
  prompt_version: string
  item_review_coverage_percentage: number
  scene_review_coverage_percentage: number
  hard_failure_review_coverage_percentage: number
  item_scores: BenchmarkHumanItemScoreAggregate
  scene_scores: BenchmarkHumanSceneScoreAggregate
  hard_failures: BenchmarkHardFailureAggregate
}

export interface FlattenedReviewItem {
  output: BenchmarkOutputRead
  item: BenchmarkItemRead | null
  scene: BenchmarkSceneRead
  itemEvaluation: BenchmarkItemEvaluationRead | null
  hardFailure: BenchmarkHardFailureRead | null
}
