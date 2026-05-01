import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useExplain, useModels } from './hooks/useExplain'
import { UrlInput } from './components/UrlInput'
import { PostPreview } from './components/PostPreview'
import { ExplanationCard } from './components/ExplanationCard'
import { SearchResultsPanel } from './components/SearchResultsPanel'
import { LoadingState } from './components/LoadingState'
import { ErrorBanner } from './components/ErrorBanner'
import { ModelSelect } from './components/ModelSelect'
import { EvalDashboard } from './components/EvalDashboard'

const queryClient = new QueryClient()

const DEFAULT_MODEL = 'gpt-4o'

type Tab = 'explainer' | 'eval'

function Shell() {
  const { data: models = [] } = useModels()
  const [tab, setTab] = useState<Tab>('explainer')

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 px-4 py-10">
      <div className="max-w-3xl mx-auto space-y-6">

        {/* Header */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-2 mb-1">
            <span className="text-2xl">🦋</span>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Bluesky Post Explainer
            </h1>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-300">
            Paste a Bluesky post URL to get an AI-powered contextual explanation.
          </p>
        </div>

        {/* Tab nav */}
        <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700">
          {(['explainer', 'eval'] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium capitalize transition-colors border-b-2 -mb-px ${
                tab === t
                  ? 'border-indigo-500 text-indigo-500 dark:text-indigo-400'
                  : 'border-transparent text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              {t === 'eval' ? 'Evaluation' : 'Explainer'}
            </button>
          ))}
        </div>

        {tab === 'explainer' ? <ExplainerTab models={models} /> : <EvalDashboard models={models} />}

      </div>
    </div>
  )
}

function ExplainerTab({ models }: { models: string[] }) {
  const { mutate, data, isPending, error, reset } = useExplain()
  const [model, setModel] = useState(DEFAULT_MODEL)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <UrlInput onSubmit={url => mutate({ url, model })} isPending={isPending} />
        </div>
        <ModelSelect value={model} onChange={setModel} models={models} disabled={isPending} />
      </div>

      {error && (
        <ErrorBanner message={(error as Error).message} onDismiss={reset} />
      )}

      {isPending && <LoadingState />}

      {data && !isPending && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
            <PostPreview post={data.post} />
            <ExplanationCard bullets={data.bullets} />
          </div>
          <SearchResultsPanel sources={data.sources} />
        </div>
      )}

      <footer className="text-center text-xs text-gray-500 dark:text-gray-400 pt-4">
        Powered by {model} · Tavily Search · LangGraph
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Shell />
    </QueryClientProvider>
  )
}
