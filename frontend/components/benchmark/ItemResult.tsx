import type { BenchmarkOutputWithItemRead } from "@/types/benchmark"
import StatusBadge from "./StatusBadge"
import AutomaticMetricBadge from "./AutomaticMetricBadge"

interface Props {
  outputWithItem: BenchmarkOutputWithItemRead
}

export default function ItemResult({ outputWithItem }: Props) {
  const { output, item } = outputWithItem
  const score = output.score

  return (
    <div className="rounded-lg border border-zinc-100 bg-white p-4">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
            #{output.sequence_number}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-1.5">
          <StatusBadge status={output.status} />
          {item?.requires_previous_memory && (
            <span className="inline-flex items-center rounded-full border border-purple-200 bg-purple-50 px-2 py-0.5 text-xs font-medium text-purple-700">
              Mem-dep
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <p className="mb-0.5 text-xs font-medium text-zinc-400">Japanese</p>
          <p className="text-sm text-zinc-800">{item?.source_text_ja || "—"}</p>
        </div>
        <div>
          <p className="mb-0.5 text-xs font-medium text-zinc-400">Reference EN</p>
          <p className="text-sm text-zinc-800">{item?.reference_en || "—"}</p>
        </div>
        <div className="sm:col-span-2">
          <p className="mb-0.5 text-xs font-medium text-zinc-400">Model Output</p>
          <p className="text-sm text-zinc-800">
            {output.output_localized_text_en || (
              <span className="italic text-zinc-400">
                {output.status === "failed" ? output.error_message || "Failed" : "No output"}
              </span>
            )}
          </p>
        </div>
      </div>

      {item?.speaker && (
        <p className="mt-2 text-xs text-zinc-500">
          Speaker: <span className="font-medium text-zinc-700">{item.speaker}</span>
        </p>
      )}

      {output.output_literal_meaning && (
        <details className="mt-2">
          <summary className="cursor-pointer text-xs font-medium text-zinc-400 hover:text-zinc-600">
            Literal meaning & notes
          </summary>
          <div className="mt-1 space-y-1 rounded-md bg-zinc-50 p-2 text-xs text-zinc-600">
            {output.output_literal_meaning && (
              <p>Literal: {output.output_literal_meaning}</p>
            )}
            {output.output_localization_note && (
              <p>Note: {output.output_localization_note}</p>
            )}
          </div>
        </details>
      )}

      {score && (
        <div className="mt-3 flex flex-wrap gap-1.5 border-t border-zinc-100 pt-3">
          {score.chrf_score !== null && (
            <AutomaticMetricBadge label="chrF" value={score.chrf_score} />
          )}
          {score.bleu_score !== null && (
            <AutomaticMetricBadge label="BLEU" value={score.bleu_score} />
          )}
          {score.glossary_compliant !== null && (
            <AutomaticMetricBadge
              label="Glossary"
              value={score.glossary_compliant}
            />
          )}
          {score.placeholders_preserved !== null && (
            <AutomaticMetricBadge
              label="Placeholders"
              value={score.placeholders_preserved}
            />
          )}
          {score.untranslated_japanese && (
            <AutomaticMetricBadge label="Untranslated JP" value={true} />
          )}
          {score.line_id_mismatch && (
            <AutomaticMetricBadge label="Line ID mismatch" value={true} />
          )}
          {score.speaker_mismatch && (
            <AutomaticMetricBadge label="Speaker mismatch" value={true} />
          )}
        </div>
      )}
    </div>
  )
}
