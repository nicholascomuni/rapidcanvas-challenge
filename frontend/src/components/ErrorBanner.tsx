interface Props {
  message: string
  onDismiss: () => void
}

export function ErrorBanner({ message, onDismiss }: Props) {
  return (
    <div className="flex items-start gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
      <span className="flex-1">{message}</span>
      <button
        onClick={onDismiss}
        className="text-red-400 hover:text-red-600 dark:hover:text-red-200 font-bold leading-none"
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  )
}
