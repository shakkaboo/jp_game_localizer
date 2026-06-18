"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import { useParams, useRouter } from "next/navigation"
import {
  getRun,
  listItemEvaluations,
  listHardFailures,
  listSceneEvaluations,
  getHumanMetrics,
  createItemEvaluation,
  updateItemEvaluation,
  createHardFailure,
  updateHardFailure,
  createSceneEvaluation,
  updateSceneEvaluation,
} from "@/lib/benchmark-api"
import type {
  BenchmarkRunDetailRead,
  BenchmarkHumanMetricsSummary,
  BenchmarkItemEvaluationRead,
  BenchmarkHardFailureRead,
  BenchmarkSceneEvaluationRead,
  FlattenedReviewItem,
} from "@/types/benchmark"
import type {
  BenchmarkItemEvaluationUpdate,
  BenchmarkHardFailureUpdate,
  BenchmarkSceneEvaluationUpdate,
} from "@/types/benchmark"

import ModeBadge from "@/components/benchmark/ModeBadge"
import StatusBadge from "@/components/benchmark/StatusBadge"
import AutomaticMetricBadge from "@/components/benchmark/AutomaticMetricBadge"
import { LoadingState, ErrorState } from "@/components/benchmark/LoadingState"

import ReviewerLabelPanel from "@/components/benchmark/review/ReviewerLabelPanel"
import ReviewNavigation from "@/components/benchmark/review/ReviewNavigation"
import ReviewFilters from "@/components/benchmark/review/ReviewFilters"
import ItemReviewForm from "@/components/benchmark/review/ItemReviewForm"
import SceneReviewForm from "@/components/benchmark/review/SceneReviewForm"
import HardFailureForm from "@/components/benchmark/review/HardFailureForm"
import HumanMetricsPanel from "@/components/benchmark/review/HumanMetricsPanel"
import { useUnsavedWarning } from "@/components/benchmark/review/UnsavedChangesDialog"

const STORAGE_KEY = "benchmark_reviewer_label"

function normalizeLabel(label: string): string {
  return label.trim().replace(/\s+/g, " ")
}

function getSavedReviewerLabel(): string {
  if (typeof window === "undefined") return ""
  const saved = localStorage.getItem(STORAGE_KEY)
  if (!saved) return ""
  return normalizeLabel(saved)
}

const ALL_FILTERS: { key: string; label: string }[] = [
  { key: "all", label: "All" },
  { key: "item-reviewed", label: "Item Reviewed" },
  { key: "item-unreviewed", label: "Item Unreviewed" },
  { key: "memory-dependent", label: "Memory Dep" },
  { key: "failed-missing", label: "Failed/Missing" },
  { key: "hf-reviewed", label: "HF Reviewed" },
  { key: "hf-flagged", label: "HF Flagged" },
]

export default function BenchmarkReviewPage() {
  const params = useParams<{ runId: string }>()
  const router = useRouter()
  const runId = Number(params.runId)

  const [run, setRun] = useState<BenchmarkRunDetailRead | null>(null)
  const [itemEvals, setItemEvals] = useState<BenchmarkItemEvaluationRead[]>([])
  const [hardFailures, setHardFailures] = useState<BenchmarkHardFailureRead[]>([])
  const [sceneEvals, setSceneEvals] = useState<BenchmarkSceneEvaluationRead[]>([])
  const [humanMetrics, setHumanMetrics] = useState<BenchmarkHumanMetricsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [reviewerLabel, setReviewerLabel] = useState(getSavedReviewerLabel)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [activeFilter, setActiveFilter] = useState("all")
  const [sceneFilter, setSceneFilter] = useState<number | null>(null)

  const [itemDirty, setItemDirty] = useState(false)
  const [hfDirty, setHfDirty] = useState(false)
  const [sceneDirty, setSceneDirty] = useState(false)
  const anyDirty = itemDirty || hfDirty || sceneDirty

  const [savingItem, setSavingItem] = useState(false)
  const [savingHf, setSavingHf] = useState(false)
  const [savingScene, setSavingScene] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [duplicateMsg, setDuplicateMsg] = useState<string | null>(null)

  useUnsavedWarning(anyDirty)

  const loadAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [r, ie, hf, se, hm] = await Promise.all([
        getRun(runId),
        listItemEvaluations(runId),
        listHardFailures(runId),
        listSceneEvaluations(runId),
        getHumanMetrics(runId),
      ])
      setRun(r)
      setItemEvals(ie)
      setHardFailures(hf)
      setSceneEvals(se)
      setHumanMetrics(hm)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load review data")
    } finally {
      setLoading(false)
    }
  }, [runId])

  useEffect(() => {
    let cancelled = false
    const loadData = async () => {
      setLoading(true)
      setError(null)
      try {
        const [r, ie, hf, se, hm] = await Promise.all([
          getRun(runId),
          listItemEvaluations(runId),
          listHardFailures(runId),
          listSceneEvaluations(runId),
          getHumanMetrics(runId),
        ])
        if (!cancelled) {
          setRun(r)
          setItemEvals(ie)
          setHardFailures(hf)
          setSceneEvals(se)
          setHumanMetrics(hm)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load review data")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadData()
    return () => { cancelled = true }
  }, [runId])

  const flatItems: FlattenedReviewItem[] = useMemo(() => {
    if (!run) return []
    const result: FlattenedReviewItem[] = []
    const ieByOutput = new Map<number, BenchmarkItemEvaluationRead>()
    const hfByOutput = new Map<number, BenchmarkHardFailureRead>()

    for (const ie of itemEvals) {
      if (ie.reviewer_label === reviewerLabel) {
        ieByOutput.set(ie.benchmark_output_id, ie)
      }
    }
    for (const hf of hardFailures) {
      if (hf.reviewer_label === reviewerLabel) {
        hfByOutput.set(hf.benchmark_output_id, hf)
      }
    }

    for (const so of run.scenes) {
      for (const ow of so.outputs) {
        result.push({
          output: ow.output,
          item: ow.item,
          scene: ow.scene,
          itemEvaluation: ieByOutput.get(ow.output.id) ?? null,
          hardFailure: hfByOutput.get(ow.output.id) ?? null,
        })
      }
    }

    result.sort((a, b) => {
      if (a.scene.scene_number !== b.scene.scene_number) {
        return a.scene.scene_number - b.scene.scene_number
      }
      return (a.item?.sequence_number ?? 0) - (b.item?.sequence_number ?? 0)
    })

    return result
  }, [run, itemEvals, hardFailures, reviewerLabel])

  const filteredItems = useMemo(() => {
    let items = flatItems
    if (sceneFilter !== null) {
      items = items.filter((f) => f.scene.scene_number === sceneFilter)
    }
    switch (activeFilter) {
      case "item-reviewed":
        return items.filter((f) => f.itemEvaluation !== null)
      case "item-unreviewed":
        return items.filter((f) => f.itemEvaluation === null)
      case "memory-dependent":
        return items.filter((f) => f.item?.requires_previous_memory === true)
      case "failed-missing":
        return items.filter((f) => f.output.status !== "completed")
      case "hf-reviewed":
        return items.filter((f) => f.hardFailure !== null)
      case "hf-flagged": {
        const flagged = (hf: BenchmarkHardFailureRead) =>
          hf.invented_plot_information ||
          hf.missing_critical_meaning ||
          hf.wrong_speaker ||
          hf.broken_placeholder ||
          hf.major_glossary_violation ||
          hf.contradiction_with_previous_scene ||
          hf.unjustified_untranslated_japanese
        return items.filter((f) => f.hardFailure !== null && flagged(f.hardFailure))
      }
      default:
        return items
    }
  }, [flatItems, sceneFilter, activeFilter])

  const displayIndex = useMemo(() => {
    if (filteredItems.length === 0) return 0
    return Math.min(currentIndex, filteredItems.length - 1)
  }, [currentIndex, filteredItems.length])

  const current = filteredItems[displayIndex] ?? null

  const currentSceneEval = useMemo(() => {
    if (!current) return null
    return sceneEvals.find(
      (se) =>
        se.reviewer_label === reviewerLabel &&
        se.scene_id === current.scene.id
    ) ?? null
  }, [sceneEvals, reviewerLabel, current])

  const sceneOptions = useMemo(() => {
    if (!run) return []
    return run.scenes.map((s) => ({
      sceneNumber: s.scene.scene_number,
      title: s.scene.title,
    }))
  }, [run])

  const handleLabelChange = useCallback((label: string) => {
    setReviewerLabel(label)
  }, [])

  const handlePrev = useCallback(() => {
    if (currentIndex > 0) setCurrentIndex(currentIndex - 1)
  }, [currentIndex])

  const handleNext = useCallback(() => {
    if (currentIndex < filteredItems.length - 1) setCurrentIndex(currentIndex + 1)
  }, [currentIndex, filteredItems.length])

  const handleSceneChange = useCallback((sceneNumber: number) => {
    if (sceneNumber === 0) {
      setSceneFilter(null)
    } else {
      setSceneFilter(sceneNumber)
    }
  }, [])

  const handleJumpToFirstUnreviewed = useCallback(() => {
    const idx = filteredItems.findIndex((f) => f.itemEvaluation === null)
    if (idx >= 0) setCurrentIndex(idx)
  }, [filteredItems])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      const isTextInput =
        target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable
      if (isTextInput) return

      if (e.shiftKey && e.key === "ArrowLeft") {
        e.preventDefault()
        handlePrev()
      }
      if (e.shiftKey && e.key === "ArrowRight") {
        e.preventDefault()
        handleNext()
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault()
        if (itemDirty && !savingItem) {
          const saveBtn = document.querySelector('[data-save-item]') as HTMLButtonElement
          saveBtn?.click()
        }
        if (hfDirty && !savingHf) {
          const saveBtn = document.querySelector('[data-save-hf]') as HTMLButtonElement
          saveBtn?.click()
        }
        if (sceneDirty && !savingScene) {
          const saveBtn = document.querySelector('[data-save-scene]') as HTMLButtonElement
          saveBtn?.click()
        }
      }
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [handlePrev, handleNext, itemDirty, hfDirty, sceneDirty, savingItem, savingHf, savingScene])

  // --- Item evaluation save handler ---
  const handleItemSave = async (values: Record<string, number | string | null>) => {
    if (!current) return
    setSavingItem(true)
    setSaveError(null)
    setDuplicateMsg(null)

    const body = {
      benchmark_output_id: current.output.id,
      reviewer_label: reviewerLabel,
      meaning_preservation: values.meaning_preservation as number,
      omission_addition_control: values.omission_addition_control as number,
      natural_english: values.natural_english as number,
      character_voice: values.character_voice as number,
      glossary_consistency: values.glossary_consistency as number,
      genre_tone_fit: values.genre_tone_fit as number,
      scene_consistency: values.scene_consistency as number,
      grammar_punctuation: values.grammar_punctuation as number,
      reviewer_notes: values.reviewer_notes as string | null,
    }

    try {
      if (current.itemEvaluation) {
        const updateBody: BenchmarkItemEvaluationUpdate = {
          meaning_preservation: body.meaning_preservation,
          omission_addition_control: body.omission_addition_control,
          natural_english: body.natural_english,
          character_voice: body.character_voice,
          glossary_consistency: body.glossary_consistency,
          genre_tone_fit: body.genre_tone_fit,
          scene_consistency: body.scene_consistency,
          grammar_punctuation: body.grammar_punctuation,
          reviewer_notes: body.reviewer_notes,
        }
        const updated = await updateItemEvaluation(current.itemEvaluation.id, updateBody)
        setItemEvals((prev) =>
          prev.map((ie) => (ie.id === updated.id ? updated : ie))
        )
      } else {
        const created = await createItemEvaluation(runId, body)
        setItemEvals((prev) => [...prev, created])
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to save"
      if (msg.includes("409") || msg.includes("Duplicate")) {
        setDuplicateMsg("Another review already exists for this output. Refreshing data...")
        const fresh = await listItemEvaluations(runId)
        setItemEvals(fresh)
        setDuplicateMsg("Existing review loaded. Your form values have been preserved — update the existing review instead.")
      } else {
        setSaveError(msg)
      }
    } finally {
      setSavingItem(false)
    }
  }

  // --- Hard-failure save handler ---
  const handleHardFailureSave = async (values: Record<string, boolean | string | null>) => {
    if (!current) return
    setSavingHf(true)
    setSaveError(null)
    setDuplicateMsg(null)

    const body = {
      benchmark_output_id: current.output.id,
      reviewer_label: reviewerLabel,
      invented_plot_information: values.invented_plot_information as boolean,
      missing_critical_meaning: values.missing_critical_meaning as boolean,
      wrong_speaker: values.wrong_speaker as boolean,
      broken_placeholder: values.broken_placeholder as boolean,
      major_glossary_violation: values.major_glossary_violation as boolean,
      contradiction_with_previous_scene: values.contradiction_with_previous_scene as boolean,
      unjustified_untranslated_japanese: values.unjustified_untranslated_japanese as boolean,
      explanation: values.explanation as string | null,
    }

    try {
      if (current.hardFailure) {
        const updateBody: BenchmarkHardFailureUpdate = {
          invented_plot_information: body.invented_plot_information,
          missing_critical_meaning: body.missing_critical_meaning,
          wrong_speaker: body.wrong_speaker,
          broken_placeholder: body.broken_placeholder,
          major_glossary_violation: body.major_glossary_violation,
          contradiction_with_previous_scene: body.contradiction_with_previous_scene,
          unjustified_untranslated_japanese: body.unjustified_untranslated_japanese,
          explanation: body.explanation,
        }
        const updated = await updateHardFailure(current.hardFailure.id, updateBody)
        setHardFailures((prev) =>
          prev.map((hf) => (hf.id === updated.id ? updated : hf))
        )
      } else {
        const created = await createHardFailure(runId, body)
        setHardFailures((prev) => [...prev, created])
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to save"
      if (msg.includes("409") || msg.includes("Duplicate")) {
        setDuplicateMsg("Another hard-failure review already exists. Refreshing...")
        const fresh = await listHardFailures(runId)
        setHardFailures(fresh)
        setDuplicateMsg("Existing hard-failure review loaded. Update the existing review instead.")
      } else {
        setSaveError(msg)
      }
    } finally {
      setSavingHf(false)
    }
  }

  // --- Scene evaluation save handler ---
  const handleSceneSave = async (values: Record<string, number | string | null>) => {
    if (!current) return
    setSavingScene(true)
    setSaveError(null)
    setDuplicateMsg(null)

    const body = {
      scene_id: current.scene.id,
      reviewer_label: reviewerLabel,
      voice_consistency: values.voice_consistency as number,
      terminology_consistency: values.terminology_consistency as number,
      emotional_progression: values.emotional_progression as number,
      relationship_continuity: values.relationship_continuity as number,
      narrative_coherence: values.narrative_coherence as number,
      genre_tone_consistency: values.genre_tone_consistency as number,
      reviewer_notes: values.reviewer_notes as string | null,
    }

    try {
      if (currentSceneEval) {
        const updateBody: BenchmarkSceneEvaluationUpdate = {
          voice_consistency: body.voice_consistency,
          terminology_consistency: body.terminology_consistency,
          emotional_progression: body.emotional_progression,
          relationship_continuity: body.relationship_continuity,
          narrative_coherence: body.narrative_coherence,
          genre_tone_consistency: body.genre_tone_consistency,
          reviewer_notes: body.reviewer_notes,
        }
        const updated = await updateSceneEvaluation(currentSceneEval.id, updateBody)
        setSceneEvals((prev) =>
          prev.map((se) => (se.id === updated.id ? updated : se))
        )
      } else {
        const created = await createSceneEvaluation(runId, body)
        setSceneEvals((prev) => [...prev, created])
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to save"
      if (msg.includes("409") || msg.includes("Duplicate")) {
        setDuplicateMsg("Another scene review already exists. Refreshing...")
        const fresh = await listSceneEvaluations(runId)
        setSceneEvals(fresh)
        setDuplicateMsg("Existing scene review loaded. Update it instead.")
      } else {
        setSaveError(msg)
      }
    } finally {
      setSavingScene(false)
    }
  }

  const load = useCallback(() => {
    loadAll()
  }, [loadAll])

  const filterOptions = useMemo(() => {
    if (!run) return ALL_FILTERS
    const sceneFilters = run.scenes.map((s) => ({
      key: `scene-${s.scene.scene_number}`,
      label: `Scene ${s.scene.scene_number}`,
    }))
    return [...ALL_FILTERS, ...sceneFilters]
  }, [run])

  const isFilterScene = (key: string) => key.startsWith("scene-")

  const handleFilterChange = (key: string) => {
    if (isFilterScene(key)) {
      const num = Number(key.replace("scene-", ""))
      if (sceneFilter !== num) {
        setSceneFilter(num)
        setActiveFilter("all")
      }
    } else {
      setActiveFilter(key)
      setSceneFilter(null)
    }
  }

  if (loading) return <LoadingState message="Loading review data..." />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!run) return <LoadingState message="Run not found." />

  const unreviewedCount = filteredItems.filter((f) => f.itemEvaluation === null).length

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <button
        type="button"
        onClick={() => router.push(`/benchmark/runs/${runId}`)}
        className="mb-4 text-sm text-zinc-400 hover:text-zinc-600"
      >
        &larr; Back to Run #{runId}
      </button>

      <div className="mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-zinc-900">
            Review Run #{run.id}
          </h1>
          <ModeBadge mode={run.mode} />
          <StatusBadge status={run.status} />
        </div>
        <p className="mt-1 text-sm text-zinc-500">
          {run.llm_provider} / {run.llm_model} &middot; {run.total_scenes} scenes,{" "}
          {flatItems.length} outputs
        </p>
      </div>

      <ReviewerLabelPanel
        reviewerLabel={reviewerLabel}
        onLabelChange={handleLabelChange}
      />

      {!reviewerLabel && (
        <div className="mb-8 rounded-xl border border-zinc-200 bg-zinc-50 p-10 text-center text-sm text-zinc-400">
          Enter a reviewer label above to begin reviewing.
        </div>
      )}

      {reviewerLabel && (
        <>
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <ReviewNavigation
              onPrev={handlePrev}
              onNext={handleNext}
              currentIndex={currentIndex}
              totalItems={filteredItems.length}
              onJumpToFirstUnreviewed={handleJumpToFirstUnreviewed}
              hasUnreviewedItems={unreviewedCount > 0}
              onSceneChange={handleSceneChange}
              scenes={sceneOptions}
              currentSceneNumber={sceneFilter ?? 0}
              isDirty={anyDirty}
            />
          </div>

          <div className="mb-6">
            <ReviewFilters
              filters={filterOptions}
              activeFilter={sceneFilter !== null ? `scene-${sceneFilter}` : activeFilter}
              onFilterChange={handleFilterChange}
              isDirty={anyDirty}
            />
          </div>

          {filteredItems.length === 0 && (
            <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-10 text-center text-sm text-zinc-400">
              No items match the current filter.
            </div>
          )}

          {current && (
            <div className="grid gap-6 lg:grid-cols-5">
              {/* Left column — output display */}
              <div className="space-y-4 lg:col-span-3">
                <div className="rounded-xl border border-zinc-200 bg-white p-5">
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                        Scene {current.scene.scene_number} &middot; #{current.output.sequence_number}
                      </p>
                      <p className="text-sm font-medium text-zinc-700">
                        {current.scene.title || `Scene ${current.scene.scene_number}`}
                      </p>
                      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-zinc-500">
                        <span>{current.scene.genre}</span>
                        <span>{current.scene.content_type}</span>
                        {current.scene.tone && <span>Tone: {current.scene.tone}</span>}
                      </div>
                    </div>
                    <div className="flex shrink-0 flex-wrap gap-1.5">
                      <StatusBadge status={current.output.status} />
                      {current.item?.requires_previous_memory && (
                        <span className="inline-flex items-center rounded-full border border-purple-200 bg-purple-50 px-2 py-0.5 text-xs font-medium text-purple-700">
                          Mem-dep
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <p className="mb-0.5 text-xs font-medium text-zinc-400">Japanese Source</p>
                      <p className="text-sm text-zinc-800">{current.item?.source_text_ja || "—"}</p>
                    </div>
                    <div>
                      <p className="mb-0.5 text-xs font-medium text-zinc-400">Reference English</p>
                      <p className="text-sm text-zinc-800">{current.item?.reference_en || "—"}</p>
                    </div>
                    <div className="sm:col-span-2">
                      <p className="mb-0.5 text-xs font-medium text-zinc-400">Model Output</p>
                      <p className="text-sm text-zinc-800">
                        {current.output.output_localized_text_en || (
                          <span className="italic text-zinc-400">
                            {current.output.status === "failed"
                              ? current.output.error_message || "Failed"
                              : "No output"}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  {current.item?.speaker && (
                    <p className="mt-2 text-xs text-zinc-500">
                      Speaker: <span className="font-medium text-zinc-700">{current.item.speaker}</span>
                    </p>
                  )}

                  {(current.output.output_literal_meaning || current.output.output_localization_note) && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-xs font-medium text-zinc-400 hover:text-zinc-600">
                        Literal meaning &amp; notes
                      </summary>
                      <div className="mt-1 space-y-1 rounded-md bg-zinc-50 p-2 text-xs text-zinc-600">
                        {current.output.output_literal_meaning && (
                          <p>Literal: {current.output.output_literal_meaning}</p>
                        )}
                        {current.output.output_localization_note && (
                          <p>Note: {current.output.output_localization_note}</p>
                        )}
                      </div>
                    </details>
                  )}

                  {/* Error category */}
                  {current.output.error_message && (
                    <div className="mt-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                      Error: {current.output.error_message}
                    </div>
                  )}

                  {/* Automatic metrics */}
                  {current.output.score && (
                    <div className="mt-3 border-t border-zinc-100 pt-3">
                      <p className="mb-2 text-xs font-medium text-zinc-500">Automatic Metrics</p>
                      <p className="mb-2 text-xs italic text-zinc-400">
                        Automatic metrics are supporting signals. Human review should judge meaning,
                        voice, tone, terminology, and scene consistency.
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {current.output.score.chrf_score !== null && (
                          <AutomaticMetricBadge label="chrF" value={current.output.score.chrf_score} />
                        )}
                        {current.output.score.bleu_score !== null && (
                          <AutomaticMetricBadge label="BLEU" value={current.output.score.bleu_score} />
                        )}
                        {current.output.score.glossary_compliant !== null && (
                          <AutomaticMetricBadge label="Glossary" value={current.output.score.glossary_compliant} />
                        )}
                        {current.output.score.placeholders_preserved !== null && (
                          <AutomaticMetricBadge label="Placeholders" value={current.output.score.placeholders_preserved} />
                        )}
                        {current.output.score.untranslated_japanese && (
                          <AutomaticMetricBadge label="Untranslated JP" value={true} />
                        )}
                        {current.output.score.line_id_mismatch && (
                          <AutomaticMetricBadge label="Line ID mismatch" value={true} />
                        )}
                        {current.output.score.speaker_mismatch && (
                          <AutomaticMetricBadge label="Speaker mismatch" value={true} />
                        )}
                      </div>
                    </div>
                  )}

                  {/* Item evaluation done indicator */}
                  {current.itemEvaluation && (
                    <div className="mt-3 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-xs text-green-700">
                      Item reviewed &middot; Total: {current.itemEvaluation.total_score} / 100
                    </div>
                  )}

                  {/* Hard failure done indicator */}
                  {current.hardFailure && (
                    <div className="mt-2 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
                      Hard-failure reviewed
                      {(current.hardFailure.invented_plot_information ||
                        current.hardFailure.missing_critical_meaning ||
                        current.hardFailure.wrong_speaker ||
                        current.hardFailure.broken_placeholder ||
                        current.hardFailure.major_glossary_violation ||
                        current.hardFailure.contradiction_with_previous_scene ||
                        current.hardFailure.unjustified_untranslated_japanese) && (
                        <span className="ml-1 text-red-600"> &middot; Issues flagged</span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Right column — forms */}
              <div className="space-y-6 lg:col-span-2">
                {saveError && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {saveError}
                  </div>
                )}

                {duplicateMsg && (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                    {duplicateMsg}
                  </div>
                )}

                {/* Item Review Form */}
                <div className="rounded-xl border border-zinc-200 bg-white p-5">
                  <ItemReviewForm
                    defaultValues={{
                      meaning_preservation: current.itemEvaluation?.meaning_preservation ?? 0,
                      omission_addition_control: current.itemEvaluation?.omission_addition_control ?? 0,
                      natural_english: current.itemEvaluation?.natural_english ?? 0,
                      character_voice: current.itemEvaluation?.character_voice ?? 0,
                      glossary_consistency: current.itemEvaluation?.glossary_consistency ?? 0,
                      genre_tone_fit: current.itemEvaluation?.genre_tone_fit ?? 0,
                      scene_consistency: current.itemEvaluation?.scene_consistency ?? 0,
                      grammar_punctuation: current.itemEvaluation?.grammar_punctuation ?? 0,
                      reviewer_notes: current.itemEvaluation?.reviewer_notes ?? null,
                    }}
                    existingEvaluation={current.itemEvaluation}
                    outputStatus={current.output.status}
                    onSave={handleItemSave}
                    onDirtyChange={setItemDirty}
                  />
                </div>

                {/* Hard Failure Form */}
                <div className="rounded-xl border border-zinc-200 bg-white p-5">
                  <HardFailureForm
                    defaultValues={{
                      invented_plot_information: current.hardFailure?.invented_plot_information ?? false,
                      missing_critical_meaning: current.hardFailure?.missing_critical_meaning ?? false,
                      wrong_speaker: current.hardFailure?.wrong_speaker ?? false,
                      broken_placeholder: current.hardFailure?.broken_placeholder ?? false,
                      major_glossary_violation: current.hardFailure?.major_glossary_violation ?? false,
                      contradiction_with_previous_scene: current.hardFailure?.contradiction_with_previous_scene ?? false,
                      unjustified_untranslated_japanese: current.hardFailure?.unjustified_untranslated_japanese ?? false,
                      explanation: current.hardFailure?.explanation ?? null,
                    }}
                    existingFailure={current.hardFailure}
                    onSave={handleHardFailureSave}
                    onDirtyChange={setHfDirty}
                  />
                </div>

                {/* Scene Review Form */}
                <div className="rounded-xl border border-zinc-200 bg-white p-5">
                  <p className="mb-3 text-xs text-zinc-400">
                    Scene: {current.scene.title || `Scene ${current.scene.scene_number}`}
                    {currentSceneEval && (
                      <span className="ml-2 text-green-600">
                        Saved total: {currentSceneEval.total_score} / 100
                      </span>
                    )}
                  </p>
                  <SceneReviewForm
                    defaultValues={{
                      voice_consistency: currentSceneEval?.voice_consistency ?? 0,
                      terminology_consistency: currentSceneEval?.terminology_consistency ?? 0,
                      emotional_progression: currentSceneEval?.emotional_progression ?? 0,
                      relationship_continuity: currentSceneEval?.relationship_continuity ?? 0,
                      narrative_coherence: currentSceneEval?.narrative_coherence ?? 0,
                      genre_tone_consistency: currentSceneEval?.genre_tone_consistency ?? 0,
                      reviewer_notes: currentSceneEval?.reviewer_notes ?? null,
                    }}
                    existingEvaluation={currentSceneEval}
                    onSave={handleSceneSave}
                    onDirtyChange={setSceneDirty}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Human Metrics */}
          {humanMetrics && (
            <div className="mt-8">
              <h2 className="mb-4 text-xl font-semibold text-zinc-800">
                Human Review Metrics
              </h2>
              <HumanMetricsPanel metrics={humanMetrics} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
