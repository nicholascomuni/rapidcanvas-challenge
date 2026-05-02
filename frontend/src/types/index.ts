export interface BulletPoint {
  text: string
}

export interface PostMeta {
  author_handle: string
  text: string
  image_url: string | null
}

export interface ExplainResponse {
  post: PostMeta
  bullets: BulletPoint[]
  sources: string[]
}

export interface JudgeDimension {
  score: number
  reason: string
}

export interface EvalCaseResult {
  id: string
  skipped: boolean
  live_fetch?: boolean
  bullets_explanation_similarity?: number | null
  bullets_context_similarity?: number | null
  search_query_similarity?: number | null
  citation?: number | null
  bullet_count?: number | null
  judge_score?: number
  evaluation_score?: number
  judge_detail?: Record<string, JudgeDimension>
  bullets?: string[]
  post?: PostMeta | null
}

export interface EvalAggregate {
  bullets_explanation_similarity?: number | null
  bullets_context_similarity?: number | null
  search_query_similarity?: number | null
  citation?: number | null
  bullet_count?: number | null
  judge_score?: number | null
  evaluation_score?: number | null
}

export interface EvalReport {
  aggregate: EvalAggregate
  cases: EvalCaseResult[]
  conclusion: string
}

export type EvalStreamEvent =
  | { event: 'start'; data: { total: number } }
  | { event: 'case_start'; data: { id: string; index: number; total: number } }
  | { event: 'case_done'; data: EvalCaseResult }
  | { event: 'conclusion_start'; data: Record<string, never> }
  | { event: 'done'; data: { aggregate: EvalAggregate; conclusion: string } }
