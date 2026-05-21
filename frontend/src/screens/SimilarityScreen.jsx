import { useState } from 'react'
import { Button, Card, Label, Icon, Input, Spinner } from '../components/primitives'
import Heatmap from '../components/Heatmap'
import { SuspiciousPair } from '../components/DetailSidebar'
import Dropzone from '../components/Dropzone'
import { computeSimilarity } from '../api/client'

export default function SimilarityScreen() {
  const [files, setFiles] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [threshold, setThreshold] = useState(0.70)

  const run = async () => {
    if (files.length < 2) { setError('Need at least 2 files to compare.'); return }
    setLoading(true); setError(null)
    const submissions = await Promise.all(files.map(async f => ({
      id: f.name.replace(/\.[^.]+$/, ''),
      code: await f.text(),
    })))
    try {
      const data = await computeSimilarity(submissions)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const suspiciousPairs = result?.suspicious_pairs?.filter(p => p.similarity >= threshold) || []

  return (
    <div style={{ padding: '40px 80px 80px', maxWidth: 1280, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <Label style={{ marginBottom: 8 }}>Cross-submission analysis</Label>
        <h1 style={{ fontSize: 40, fontWeight: 700, letterSpacing: '-0.02em', color: '#F8FAFC', margin: 0, lineHeight: 1.1 }}>
          Submission similarity
        </h1>
        <p style={{ fontSize: 15, color: '#94A3B8', marginTop: 12, marginBottom: 0, maxWidth: 640 }}>
          High similarity between submissions may indicate shared AI prompts. Pairs above the threshold are surfaced below the heatmap.
        </p>
      </div>

      {!result && (
        <div style={{ marginBottom: 24 }}>
          <Dropzone files={files} onUpload={f => { setFiles(Array.from(f)); setResult(null); setError(null) }}/>
          {files.length >= 2 && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
              <Button variant="primary" icon="play" onClick={run} disabled={loading}>
                {loading ? 'Computing…' : `Compare ${files.length} submissions`}
              </Button>
            </div>
          )}
        </div>
      )}

      {loading && (
        <Card style={{ padding: 40, textAlign: 'center' }}>
          <Spinner size={40} style={{ margin: '0 auto 16px' }}/>
          <div style={{ fontSize: 14, color: '#94A3B8' }}>Computing pairwise similarity…</div>
        </Card>
      )}

      {error && (
        <Card style={{ padding: 20, marginBottom: 24, borderColor: 'rgba(239,68,68,0.35)' }}>
          <div style={{ display: 'flex', gap: 10 }}><Icon name="alert" size={16} color="#EF4444"/><span style={{ color: '#EF4444', fontSize: 14 }}>{error}</span></div>
        </Card>
      )}

      {result && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 24, alignItems: 'start', marginBottom: 40 }}>
            <Card style={{ padding: 24 }}>
              <Heatmap ids={result.ids} data={result.matrix}/>
            </Card>

            <Card style={{ padding: 18 }}>
              <Label style={{ marginBottom: 14 }}>Filters</Label>
              <div style={{ marginBottom: 18 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: 12, color: '#CBD5E1' }}>Similarity threshold</span>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#00D4FF', fontWeight: 600 }}>{Math.round(threshold * 100)}%</span>
                </div>
                <input type="range" min="0" max="100" value={Math.round(threshold * 100)}
                  onChange={e => setThreshold(e.target.value / 100)}
                  style={{ width: '100%', accentColor: '#00D4FF' }}/>
              </div>
              <div style={{ padding: '12px 14px', background: 'rgba(0,212,255,0.06)', borderRadius: 8, border: '1px solid rgba(0,212,255,0.15)' }}>
                <div style={{ fontSize: 12, color: '#94A3B8', marginBottom: 4 }}>Suspicious pairs</div>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 24, fontWeight: 700, color: suspiciousPairs.length > 0 ? '#EF4444' : '#10B981' }}>
                  {suspiciousPairs.length}
                </div>
              </div>
              <div style={{ marginTop: 14 }}>
                <Button variant="secondary" size="sm" icon="upload" onClick={() => { setResult(null); setFiles([]) }} style={{ width: '100%' }}>
                  Re-upload
                </Button>
              </div>
            </Card>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 18 }}>
              <h2 style={{ fontSize: 24, fontWeight: 600, color: '#F8FAFC', margin: 0, letterSpacing: '-0.01em' }}>Suspicious pairs</h2>
              <span style={{ fontSize: 12, color: '#64748B' }}>{suspiciousPairs.length} pairs above {Math.round(threshold * 100)}%</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {suspiciousPairs.map((p, i) => (
                <SuspiciousPair key={i} a={p.id_a} b={p.id_b} similarity={Math.round(p.similarity * 100)}/>
              ))}
              {suspiciousPairs.length === 0 && (
                <Card style={{ padding: 40, textAlign: 'center' }}>
                  <Icon name="check" size={32} color="#10B981"/>
                  <div style={{ fontSize: 14, color: '#94A3B8', marginTop: 10 }}>No pairs exceed the {Math.round(threshold * 100)}% threshold</div>
                </Card>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
