// api/client.js — sve API pozive na Flask backend

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

// Analiza više kodova odjednom
export const analyzeBatch = (submissions) =>
  request('POST', '/analyze-batch', { submissions })

// Matrica sličnosti
export const computeSimilarity = (submissions) =>
  request('POST', '/similarity', { submissions })
