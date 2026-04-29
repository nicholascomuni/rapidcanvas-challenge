import { useState, type FormEvent } from 'react'

interface Props {
  onSubmit: (url: string) => void
  isPending: boolean
}

const BSKY_PATTERN = /^https?:\/\/bsky\.app\/profile\/[^/]+\/post\/[A-Za-z0-9]+$/

export function UrlInput({ onSubmit, isPending }: Props) {
  const [value, setValue] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = value.trim()
    if (!BSKY_PATTERN.test(trimmed)) {
      setError('Please enter a valid Bluesky post URL (e.g. https://bsky.app/profile/user.bsky.social/post/abc123)')
      return
    }
    setError('')
    onSubmit(trimmed)
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          type="url"
          value={value}
          onChange={e => { setValue(e.target.value); setError('') }}
          placeholder="https://bsky.app/profile/user.bsky.social/post/..."
          className="flex-1 px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm"
          disabled={isPending}
          autoFocus
        />
        <button
          type="submit"
          disabled={isPending || !value.trim()}
          className="px-6 py-3 rounded-xl bg-sky-500 hover:bg-sky-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors whitespace-nowrap"
        >
          {isPending ? 'Explaining…' : 'Explain post'}
        </button>
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-500">{error}</p>
      )}
    </form>
  )
}
