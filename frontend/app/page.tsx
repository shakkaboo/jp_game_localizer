"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import FileUploadCard from "@/components/FileUploadCard"
import {
  uploadContext,
  uploadScript,
  createChunks,
} from "@/lib/api"
import type {
  ContextUploadResponse,
  ScriptUploadResponse,
} from "@/types"

export default function UploadPage() {
  const router = useRouter()

  const [contextResult, setContextResult] =
    useState<ContextUploadResponse | null>(null)
  const [scriptResult, setScriptResult] =
    useState<ScriptUploadResponse | null>(null)
  const [chunksCreated, setChunksCreated] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const projectId = contextResult?.project_id ?? null

  const handleContextUpload = async (file: File) => {
    setError(null)
    try {
      const res = await uploadContext(file)
      setContextResult(res)
      localStorage.setItem("project_id", String(res.project_id))
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed")
    }
  }

  const handleScriptUpload = async (file: File) => {
    setError(null)
    if (!projectId) {
      setError("Upload context first to get a project ID.")
      return
    }
    try {
      const res = await uploadScript(projectId, file)
      setScriptResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed")
    }
  }

  const handleCreateChunks = async () => {
    if (!projectId) return
    setError(null)
    setCreating(true)
    try {
      await createChunks(projectId)
      setChunksCreated(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create chunks")
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-2 text-3xl font-bold text-zinc-900">
        Game Localization
      </h1>
      <p className="mb-10 text-zinc-500">
        Upload your game context and script to get started.
      </p>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mb-8 grid gap-6 sm:grid-cols-2">
        <FileUploadCard
          title="Context File"
          accept=".json,.yaml,.yml,.txt,.docx"
          description="Game world, characters, glossary, and style rules."
          onUpload={handleContextUpload}
        />
        <FileUploadCard
          title="Script File"
          accept=".csv,.xlsx,.xls,.txt,.json"
          description="Japanese dialogue lines with character names."
          onUpload={handleScriptUpload}
        />
      </div>

      {contextResult && !chunksCreated && (
        <div className="mb-8">
          <button
            type="button"
            onClick={handleCreateChunks}
            disabled={creating}
            className="rounded-xl bg-zinc-900 px-8 py-3 text-base font-semibold text-white transition-colors hover:bg-zinc-700 disabled:opacity-50"
          >
            {creating
              ? "Creating chunks..."
              : scriptResult
                ? "Create Scene Chunks & Start Project"
                : "Upload a script file too, then create chunks"}
          </button>
        </div>
      )}

      {contextResult && (
        <SummaryCard title="Context">
          <p>
            <span className="text-zinc-500">Project:</span>{" "}
            {contextResult.project?.title || "Untitled"}
            {contextResult.project?.genre && (
              <>
                {" · "}
                <span className="text-zinc-500">Genre:</span>{" "}
                {contextResult.project.genre}
              </>
            )}
          </p>
          <p>
            <span className="text-zinc-500">File type:</span>{" "}
            {contextResult.file_type}
          </p>
          {contextResult.sections.length > 0 && (
            <p>
              <span className="text-zinc-500">Sections:</span>{" "}
              {contextResult.sections.join(", ")}
            </p>
          )}
          {contextResult.warnings.length > 0 && (
            <Warnings warnings={contextResult.warnings} />
          )}
        </SummaryCard>
      )}

      {scriptResult && (
        <SummaryCard title="Script">
          <p>
            <span className="text-zinc-500">Lines:</span>{" "}
            {scriptResult.total_lines}
          </p>
          {scriptResult.detected_characters.length > 0 && (
            <p>
              <span className="text-zinc-500">Characters:</span>{" "}
              {scriptResult.detected_characters.join(", ")}
            </p>
          )}
          {scriptResult.detected_scene_hints.length > 0 && (
            <p>
              <span className="text-zinc-500">Scenes:</span>{" "}
              {scriptResult.detected_scene_hints.join(", ")}
            </p>
          )}
          {scriptResult.warnings.length > 0 && (
            <Warnings warnings={scriptResult.warnings} />
          )}
        </SummaryCard>
      )}

      {chunksCreated && (
        <div className="rounded-xl border border-green-200 bg-green-50 p-6 text-center">
          <p className="mb-1 text-lg font-semibold text-green-800">
            Project ready!
          </p>
          <p className="mb-4 text-sm text-green-600">
            Scene chunks have been created from your script.
          </p>
          <button
            type="button"
            onClick={() => router.push("/progress")}
            className="rounded-lg bg-green-700 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-green-600"
          >
            Go to Progress
          </button>
        </div>
      )}

      {!contextResult && !scriptResult && !chunksCreated && (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-10 text-center">
          <p className="text-sm text-zinc-400">
            Upload a context file to begin.
          </p>
        </div>
      )}
    </div>
  )
}

function SummaryCard({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="mb-4 rounded-xl border border-zinc-200 bg-white p-5">
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-zinc-400">
        {title}
      </h2>
      <div className="space-y-1 text-sm text-zinc-700">{children}</div>
    </div>
  )
}

function Warnings({ warnings }: { warnings: string[] }) {
  return (
    <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
      {warnings.map((w, i) => (
        <p key={i}>{w}</p>
      ))}
    </div>
  )
}
