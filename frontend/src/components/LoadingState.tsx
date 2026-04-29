import { useEffect, useState } from 'react'

const STEPS = [
  'Fetching post from Bluesky…',
  'Generating search queries…',
  'Searching the web…',
  'Reranking results…',
  'Synthesizing explanation…',
]

export function LoadingState() {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const intervals = STEPS.map((_, i) =>
      setTimeout(() => setStep(i), i * 2200)
    )
    return () => intervals.forEach(clearTimeout)
  }, [])

  return (
    <div className="flex flex-col items-center gap-4 py-12">
      <div className="w-8 h-8 border-4 border-sky-500 border-t-transparent rounded-full animate-spin" />
      <div className="flex flex-col gap-2 w-full max-w-sm">
        {STEPS.map((label, i) => (
          <div
            key={label}
            className={`flex items-center gap-2 text-sm transition-opacity duration-300 ${
              i <= step ? 'opacity-100' : 'opacity-30'
            }`}
          >
            <span
              className={`w-4 h-4 rounded-full flex-shrink-0 ${
                i < step
                  ? 'bg-sky-500'
                  : i === step
                  ? 'bg-sky-400 animate-pulse'
                  : 'bg-gray-200 dark:bg-gray-700'
              }`}
            />
            <span className={i <= step ? 'text-gray-800 dark:text-gray-200' : 'text-gray-400'}>
              {label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
