import { useState } from 'react'

interface Props {
  sources: string[]
}

function domainOf(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

export function SearchResultsPanel({ sources }: Props) {
  const [open, setOpen] = useState(false)

  if (sources.length === 0) return null

  return (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      >
        <span>Sources ({sources.length})</span>
        <span className={`transition-transform duration-200 ${open ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {open && (
        <div className="border-t border-gray-100 dark:border-gray-800 divide-y divide-gray-100 dark:divide-gray-800">
          {sources.map((url) => (
            <div key={url} className="px-5 py-3.5">
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-sky-600 dark:text-sky-400 hover:underline truncate block"
              >
                {domainOf(url)}
              </a>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5 truncate">{url}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
