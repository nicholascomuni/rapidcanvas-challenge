import type { EvalStreamEvent } from '../types'

export async function* runEval(model: string): AsyncGenerator<EvalStreamEvent> {
  const res = await fetch('/api/v1/eval/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model }),
  })

  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })

    const messages = buf.split('\n\n')
    buf = messages.pop() ?? ''

    for (const msg of messages) {
      if (!msg.trim()) continue
      const eventLine = msg.match(/^event: (.+)$/m)
      const dataLine = msg.match(/^data: (.+)$/m)
      if (eventLine && dataLine) {
        yield { event: eventLine[1], data: JSON.parse(dataLine[1]) } as EvalStreamEvent
      }
    }
  }
}
