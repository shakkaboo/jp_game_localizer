"use client"

import type { SourceLine, TranslationDetail } from "@/types"

interface Props {
  sourceLines: SourceLine[]
  translations: TranslationDetail[]
  onSave: (translationId: number, field: string, value: string) => void
  saving: number | null
}

export default function ReviewTable({
  sourceLines,
  translations,
  onSave,
  saving,
}: Props) {
  const txnMap = new Map<number, TranslationDetail>()
  for (const t of translations) {
    txnMap.set(t.source_line_id, t)
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-zinc-200">
      <table className="min-w-full divide-y divide-zinc-200 text-sm">
        <thead className="bg-zinc-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-zinc-500">
              Character
            </th>
            <th className="px-4 py-3 text-left font-medium text-zinc-500">
              Japanese
            </th>
            <th className="px-4 py-3 text-left font-medium text-zinc-500">
              English
            </th>
            <th className="px-4 py-3 text-left font-medium text-zinc-500">
              Note
            </th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {sourceLines.map((sl) => {
            const txn = txnMap.get(sl.id)
            return (
              <tr key={sl.id} className="group hover:bg-zinc-50">
                <td className="px-4 py-3 font-medium text-zinc-800">
                  {sl.character}
                </td>
                <td className="px-4 py-3 text-zinc-600">
                  {sl.source_text_ja}
                </td>
                <td className="px-4 py-3">
                  <EditableCell
                    value={txn?.final_text_en || ""}
                    field="final_text_en"
                    translationId={txn?.id || null}
                    onSave={onSave}
                    saving={saving}
                  />
                </td>
                <td className="px-4 py-3">
                  <EditableCell
                    value={txn?.localization_note || ""}
                    field="localization_note"
                    translationId={txn?.id || null}
                    onSave={onSave}
                    saving={saving}
                  />
                </td>
                <td className="px-4 py-3 text-right">
                  {!txn && (
                    <span className="text-xs text-zinc-400">
                      Not translated
                    </span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function EditableCell({
  value,
  field,
  translationId,
  onSave,
  saving,
}: {
  value: string
  field: string
  translationId: number | null
  onSave: (translationId: number, field: string, value: string) => void
  saving: number | null
}) {
  if (!translationId) {
    return <span className="text-zinc-300 italic">—</span>
  }

  const handleBlur = (e: React.FocusEvent<HTMLTextAreaElement>) => {
    const newVal = e.target.value
    if (newVal !== value) {
      onSave(translationId, field, newVal)
    }
  }

  return (
    <div className="relative">
      <textarea
        defaultValue={value}
        onBlur={handleBlur}
        rows={2}
        className="w-full resize-none rounded-md border border-transparent bg-transparent px-2 py-1 text-zinc-800 outline-none transition-colors hover:border-zinc-200 focus:border-blue-300 focus:bg-white"
      />
      {saving === translationId && (
        <span className="absolute -right-2 -top-2 text-xs text-blue-500">
          saving...
        </span>
      )}
    </div>
  )
}
