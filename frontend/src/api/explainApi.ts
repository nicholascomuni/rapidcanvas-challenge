import type { ExplainResponse } from '../types'

export async function explainPost(url: string): Promise<ExplainResponse> {
  const res = await fetch('/api/v1/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
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
