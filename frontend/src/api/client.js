// api/client.js — svi API pozivi na Flask backend

const BASE = '/api'

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.error || `HTTP ${res.status}`)
  }
  return res.json()
}

// Provjera statusa servera
export const checkHealth = () => request('GET', '/health')

// Analiza jednog isječka koda
export const analyzeCode = (code, language, filename) =>
  request('POST', '/analyze', { code, language, filename })

/**
 * Batch analiza s real-time streamingom.
 *
 * Umjesto da čeka sve rezultate (što uzrokuje timeout),
 * čita NDJSON stream i poziva callback za svaki rezultat
 * čim stigne s backenda.
 *
 * @param {Array}    submissions  - lista { id, file, code }
 * @param {Function} onResult     - poziva se za svaki gotov fajl: (result, index, total) => void
 * @param {Function} onProgress   - poziva se s postotkom napretka: (pct) => void
 * @returns {Promise<Object>}     - summary objekt na kraju
 */
export async function analyzeBatch(submissions, onResult, onProgress) {
  const res = await fetch(`${BASE}/analyze-batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ submissions }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.error || `HTTP ${res.status}`)
  }

  // Čitamo stream liniju po liniju
  const reader  = res.body.getReader()
  const decoder = new TextDecoder()
  let   buffer  = ''
  let   count   = 0
  let   summary = null
  const total   = submissions.length

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')

    // Sve linije osim zadnje su kompletne
    buffer = lines.pop()

    for (const line of lines) {
      if (!line.trim()) continue
      try {
        const msg = JSON.parse(line)

        if (msg.type === 'result') {
          count++
          if (onResult)   onResult(msg.data, count, total)
          if (onProgress) onProgress(Math.round((count / total) * 100))
        }

        if (msg.type === 'summary') {
          summary = msg.data
        }
      } catch {
        // Ignoriraj neispravne linije
      }
    }
  }

  return summary || { total: count }
}

// Matrica sličnosti
export const computeSimilarity = (submissions) =>
  request('POST', '/similarity', { submissions })
