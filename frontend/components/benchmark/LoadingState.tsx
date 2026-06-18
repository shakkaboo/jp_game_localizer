interface LoadingProps {
  message?: string
}

export function LoadingState({ message = "Loading..." }: LoadingProps) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-24 text-center text-zinc-500">
      {message}
    </div>
  )
}

interface EmptyStateProps {
  message: string
  action?: { label: string; onClick: () => void }
}

export function EmptyState({ message, action }: EmptyStateProps) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-24 text-center">
      <p className="text-zinc-400">{message}</p>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-4 rounded-lg bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}

interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-24 text-center">
      <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
        {message}
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-lg bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
        >
          Retry
        </button>
      )}
    </div>
  )
}
