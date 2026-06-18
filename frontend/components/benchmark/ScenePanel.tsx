"use client"

import { useState } from "react"
import type { BenchmarkRunSceneOutput } from "@/types/benchmark"
import ItemResult from "./ItemResult"

interface Props {
  sceneOutput: BenchmarkRunSceneOutput
  defaultOpen?: boolean
}

export default function ScenePanel({ sceneOutput, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen)
  const { scene, outputs } = sceneOutput

  const total = outputs.length
  const completed = outputs.filter((o) => o.output.status === "completed").length
  const failed = total - completed

  return (
    <div className="rounded-xl border border-zinc-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-5 py-4 text-left"
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-xs font-bold text-zinc-500">
              {scene.scene_number}
            </span>
            <h3 className="truncate text-base font-semibold text-zinc-800">
              {scene.title || `Scene ${scene.scene_number}`}
            </h3>
          </div>
          <div className="mt-1 ml-10 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
            <span>{scene.genre}</span>
            <span>{scene.content_type}</span>
            {scene.tone && <span>{scene.tone}</span>}
            <span>
              {completed}/{total} completed
            </span>
            {failed > 0 && (
              <span className="text-red-500">{failed} failed</span>
            )}
          </div>
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className={`h-4 w-4 shrink-0 text-zinc-400 transition-transform ${
            open ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="border-t border-zinc-100 px-5 py-4">
          {outputs.length === 0 ? (
            <p className="py-4 text-center text-sm text-zinc-400">
              No outputs for this scene.
            </p>
          ) : (
            <div className="space-y-3">
              {outputs.map((ow) => (
                <ItemResult key={ow.output.id} outputWithItem={ow} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
