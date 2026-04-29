import type { BulletPoint } from '../types'

interface Props {
  bullets: BulletPoint[]
}

export function ExplanationCard({ bullets }: Props) {
  return (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5 shadow-sm">
      <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-4 text-base">
        Explanation
      </h2>
      <ul className="space-y-4">
        {bullets.map((bullet, i) => (
          <li key={i} className="flex gap-3">
            <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full bg-sky-100 dark:bg-sky-900 text-sky-600 dark:text-sky-300 text-xs font-bold flex items-center justify-center">
              {i + 1}
            </span>
            <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
              {bullet.text}
            </p>
          </li>
        ))}
      </ul>
    </div>
  )
}
