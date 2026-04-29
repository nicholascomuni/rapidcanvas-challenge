import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useExplain } from './hooks/useExplain'
import { UrlInput } from './components/UrlInput'
import { PostPreview } from './components/PostPreview'
import { ExplanationCard } from './components/ExplanationCard'
import { SearchResultsPanel } from './components/SearchResultsPanel'
import { LoadingState } from './components/LoadingState'
import { ErrorBanner } from './components/ErrorBanner'

const queryClient = new QueryClient()

function Explainer() {
  const { mutate, data, isPending, error, reset } = useExplain()

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 px-4 py-10">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-2 mb-1">
            <span className="text-2xl">🦋</span>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Bluesky Post Explainer
            </h1>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Paste a Bluesky post URL to get an AI-powered contextual explanation.
          </p>
        </div>

        <UrlInput onSubmit={url => mutate(url)} isPending={isPending} />

        {error && (
          <ErrorBanner
            message={(error as Error).message}
            onDismiss={reset}
          />
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

        <footer className="text-center text-xs text-gray-400 pt-4">
          Powered by GPT-4o · Tavily Search · LangGraph
        </footer>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Explainer />
    </QueryClientProvider>
  )
}
