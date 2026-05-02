import { useState, useCallback } from 'react'
import { runEval } from '../api/evalApi'
import type { EvalReport, EvalCaseResult, EvalAggregate, JudgeDimension } from '../types'
import { ModelSelect } from './ModelSelect'

const JUDGE_DIMS = [
  'explanation_relevance',
  'faithfulness',
  'groundedness',
  'completeness',
  'clarity',
  'context_relevance',
  'search_query_relevance',
] as const

const EMB_METRICS: [keyof EvalAggregate, string][] = [
  ['evaluation_score', 'Evaluation Score'],
  ['bullets_explanation_similarity', 'Explanation Similarity'],
  ['bullets_context_similarity', 'Context Similarity'],
  ['search_query_similarity', 'Query Similarity'],
  ['citation', 'Citation Rate'],
  ['bullet_count', 'Bullet Count'],
  ['judge_score', 'LLM-Judge Score'],
]

function scoreColor(v: number, max = 1) {
  const r = v / max
  if (r >= 0.75) return 'text-green-400'
  if (r >= 0.5) return 'text-yellow-400'
  return 'text-red-400'
}

function scoreBg(v: number, max = 1) {
  const r = v / max
  if (r >= 0.75) return 'bg-green-400'
  if (r >= 0.5) return 'bg-yellow-400'
  return 'bg-red-400'
}

function MetricBar({ label, value, max = 1 }: { label: string; value: number | null | undefined; max?: number }) {
  if (value == null) {
    return (
      <div className="flex items-center gap-3 mb-2">
        <span className="text-xs text-gray-400 w-48 shrink-0">{label}</span>
        <span className="text-xs text-gray-500">N/A</span>
      </div>
    )
  }
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div className="flex items-center gap-3 mb-2">
      <span className="text-xs text-gray-300 w-48 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-600 rounded-full h-1.5 overflow-hidden">
        <div className={`h-full rounded-full ${scoreBg(value, max)}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs w-10 text-right tabular-nums font-medium ${scoreColor(value, max)}`}>
        {value.toFixed(2)}
      </span>
    </div>
  )
}

function AggregateSection({ agg }: { agg: EvalAggregate }) {
  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
        {EMB_METRICS.map(([k, label]) => {
          const v = agg[k]
          if (v == null) return null
          return (
            <div key={k} className="bg-gray-800 border border-gray-700 rounded-xl p-4">
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">{label}</div>
              <div className={`text-2xl font-bold ${scoreColor(v)}`}>{v.toFixed(3)}</div>
            </div>
          )
        })}
      </div>
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
        {EMB_METRICS.map(([k, label]) => (
          <MetricBar key={k} label={label} value={agg[k]} />
        ))}
      </div>
    </div>
  )
}

function CaseCard({ result }: { result: EvalCaseResult }) {
  const [open, setOpen] = useState(false)

  if (result.skipped) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 flex items-center justify-between">
        <span className="text-xs font-mono text-gray-400">{result.id}</span>
        <span className="text-xs text-gray-500 italic">skipped</span>
      </div>
    )
  }

  const js = result.judge_score ?? 0

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-700/50 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-200">{result.id}</span>
          <span className="text-xs bg-indigo-900/60 text-indigo-300 border border-indigo-700/50 px-2 py-0.5 rounded">live</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">eval score</span>
          <span className={`text-base font-bold ${scoreColor(result.evaluation_score ?? js)}`}>
            {(result.evaluation_score ?? js).toFixed(2)}
          </span>
          <svg
            className={`w-3.5 h-3.5 text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`}
            viewBox="0 0 20 20" fill="currentColor"
          >
            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 border-t border-gray-600/50 pt-3 space-y-4">

          {result.post && (
            <div>
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-medium">Post</div>
              <div className="rounded-xl border border-gray-600 bg-gray-900 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-7 h-7 rounded-full bg-sky-600 flex items-center justify-center text-white text-xs font-semibold shrink-0">
                    {result.post.author_handle[0]?.toUpperCase() ?? '?'}
                  </div>
                  <span className="text-xs text-gray-400">@{result.post.author_handle}</span>
                </div>
                <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
                  {result.post.text}
                </p>
                {result.post.image_url && (
                  <div className="mt-3 rounded-lg overflow-hidden border border-gray-700">
                    <img src={result.post.image_url} alt="Post image" className="w-full object-cover max-h-48" />
                  </div>
                )}
              </div>
            </div>
          )}

          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-medium">Embedding metrics</div>
            <MetricBar label="Explanation Similarity" value={result.bullets_explanation_similarity} />
            <MetricBar label="Context Similarity" value={result.bullets_context_similarity} />
            <MetricBar label="Query Similarity" value={result.search_query_similarity} />
            <MetricBar label="Citation Rate" value={result.citation} />
            <MetricBar label="Bullet Count" value={result.bullet_count} />
          </div>

          {result.judge_detail && (
            <div>
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-medium">LLM-Judge Metrics</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
                {JUDGE_DIMS.map(dim => {
                  const entry = result.judge_detail![dim] as JudgeDimension | undefined
                  if (!entry) return null
                  return (
                    <div key={dim} className="mb-2">
                      <MetricBar
                        label={dim.replace(/_/g, ' ')}
                        value={entry.score}
                        max={5}
                      />
                      {entry.reason && (
                        <p className="text-xs text-gray-500 ml-[12.5rem] -mt-1 leading-relaxed">
                          {entry.reason}
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {result.bullets && result.bullets.length > 0 && (
            <div>
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-medium">Generated bullets</div>
              <ul className="space-y-1">
                {result.bullets.map((b, i) => (
                  <li key={i} className="text-sm text-gray-300 leading-relaxed flex gap-2">
                    <span className="text-gray-500 shrink-0 mt-0.5">•</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

type RunStatus = 'idle' | 'running' | 'done' | 'error'

interface RunState {
  status: RunStatus
  progress: { current: number; total: number; currentId: string } | null
  phase: string
  error: string | null
}

const DEFAULT_MODEL = 'gpt-4o'

export function EvalDashboard({ models }: { models: string[] }) {
  const [model, setModel] = useState(DEFAULT_MODEL)
  const [report, setReport] = useState<EvalReport | null>(null)
  const [run, setRun] = useState<RunState>({ status: 'idle', progress: null, phase: '', error: null })

  const startEval = useCallback(async () => {
    setRun({ status: 'running', progress: null, phase: 'Starting…', error: null })
    setReport(null)

    const partialCases: EvalCaseResult[] = []

    try {
      for await (const event of runEval(model)) {
        if (event.event === 'start') {
          setRun(s => ({ ...s, progress: { current: 0, total: event.data.total, currentId: '' }, phase: 'Running cases…' }))
        } else if (event.event === 'case_start') {
          setRun(s => ({
            ...s,
            progress: { current: event.data.index, total: event.data.total, currentId: event.data.id },
            phase: `Running ${event.data.id}…`,
          }))
        } else if (event.event === 'case_done') {
          partialCases.push(event.data)
          setRun(s => ({
            ...s,
            progress: s.progress ? { ...s.progress, current: s.progress.current + 1 } : null,
          }))
          setReport(r => r
            ? { ...r, cases: [...partialCases] }
            : { aggregate: {}, cases: [...partialCases], conclusion: '' }
          )
        } else if (event.event === 'conclusion_start') {
          setRun(s => ({ ...s, phase: 'Generating conclusion…' }))
        } else if (event.event === 'done') {
          setReport({ aggregate: event.data.aggregate, cases: partialCases, conclusion: event.data.conclusion })
          setRun({ status: 'done', progress: null, phase: 'Complete', error: null })
        }
      }
    } catch (e) {
      setRun(s => ({ ...s, status: 'error', error: (e as Error).message }))
    }
  }, [model])

  const active = report ? report.cases.filter(c => !c.skipped).length : 0
  const skipped = report ? report.cases.filter(c => c.skipped).length : 0

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <ModelSelect value={model} onChange={setModel} models={models} disabled={run.status === 'running'} />
        <button
          onClick={startEval}
          disabled={run.status === 'running'}
          className="h-10 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors flex items-center gap-2"
        >
          {run.status === 'running' ? (
            <>
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Running…
            </>
          ) : 'Run Evaluation'}
        </button>
      </div>

      {/* Progress bar */}
      {run.status === 'running' && run.progress && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-gray-300">
            <span>{run.phase}</span>
            <span>{run.progress.current}/{run.progress.total}</span>
          </div>
          <div className="h-1.5 bg-gray-600 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-500 rounded-full transition-all duration-300"
              style={{ width: `${(run.progress.current / run.progress.total) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Error */}
      {run.error && (
        <div className="bg-red-900/30 border border-red-700 text-red-300 text-sm rounded-xl px-4 py-3">
          {run.error}
        </div>
      )}

      {/* Report */}
      {report && (
        <div className="space-y-6">
          <div className="text-xs text-gray-400">
            {active} active · {skipped} skipped · {report.cases.length} total
          </div>

          {report.conclusion && (
            <div>
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-medium">Conclusion</div>
              <div className="border-l-2 border-indigo-500 pl-4 text-sm text-gray-200 leading-relaxed bg-gray-800 border border-gray-700 rounded-r-xl py-3 pr-4">
                {report.conclusion}
              </div>
            </div>
          )}

          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-3 font-medium">Aggregate metrics</div>
            <AggregateSection agg={report.aggregate} />
          </div>

          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-3 font-medium">Cases</div>
            <div className="space-y-2">
              {report.cases.map(c => <CaseCard key={c.id} result={c} />)}
            </div>
          </div>
        </div>
      )}

      {!report && run.status === 'idle' && (
        <div className="text-center py-16 text-gray-500 text-sm">
          Run an evaluation or load the last report to see results.
        </div>
      )}
    </div>
  )
}
