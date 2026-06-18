"use client"

import { useEffect, useCallback, useRef } from "react"

export function useUnsavedWarning(dirty: boolean) {
  const dirtyRef = useRef(dirty)

  useEffect(() => {
    dirtyRef.current = dirty
  }, [dirty])

  const handleBeforeUnload = useCallback((e: BeforeUnloadEvent) => {
    if (dirtyRef.current) {
      e.preventDefault()
      e.returnValue = ""
    }
  }, [])

  useEffect(() => {
    if (dirty) {
      window.addEventListener("beforeunload", handleBeforeUnload)
    } else {
      window.removeEventListener("beforeunload", handleBeforeUnload)
    }
    return () => window.removeEventListener("beforeunload", handleBeforeUnload)
  }, [dirty, handleBeforeUnload])
}

export function confirmUnsaved(dirty: boolean, message?: string): boolean {
  if (!dirty) return true
  return confirm(message || "You have unsaved changes. Discard them?")
}
