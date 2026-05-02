import type { ExplainResponse } from '../types'

export async function fetchModels(): Promise<string[]> {
  const res = await fetch('/api/v1/models')
  if (!res.ok) return []
  return res.json()
}

export async function explainPost(url: string, model: string): Promise<ExplainResponse> {
  const res = await fetch('/api/v1/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, model }),
  })

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // ignore parse error
    }
    throw new Error(detail)
  }

  return res.json()
}
