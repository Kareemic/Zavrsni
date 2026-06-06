import { useState, useRef } from 'react'
import { Button, Card, Label, Icon, Spinner } from '../components/primitives'
import Heatmap from '../components/Heatmap'
import { SuspiciousPair } from '../components/DetailSidebar'
import Dropzone from '../components/Dropzone'
import CodeEditor from '../components/CodeEditor'
import { computeSimilarity } from '../api/client'

export default function SimilarityScreen() {
  const [files,       setFiles]       = useState([])
  const [result,      setResult]      = useState(null)
  const [submissions, setSubmissions] = useState([])   // čuvamo kod za usporedbu
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(null)
  const [threshold,   setThreshold]   = useState(0.70)
  const [selectedPair, setSelectedPair] = useState(null)  // { i, j, idA, idB, similarity }
  const compareRef = useRef(null)

  const run = async () => {
    if (files.length < 2) { setError('Potrebne su najmanje 2 datoteke.'); return }
    setLoading(true); setError(null); setSelectedPair(null)

    const subs = await Promise.all(files.map(async f => ({
      id:   f.name.replace(/\.[^.]+$/, ''),
      file: f.name,
      code: await f.text(),
    })))

    try {
      const data = await computeSimilarity(subs)
      setResult(data)
      setSubmissions(subs)    // sačuvamo kod da ga možemo prikazati
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Kad korisnik klikne na ćeliju heatmape
  const handleSelectPair = (pair) => {
    setSelectedPair(pair)
    // Scroll do usporedbe
    if (pair) {
      setTimeout(() => compareRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
    }
  }

  const suspiciousPairs = result?.suspicious_pairs?.filter(p => p.similarity >= threshold) || []

  // Pronađi kod za odabrani par
  const codeA = selectedPair ? submissions.find(s => s.id === selectedPair.idA)?.code || '' : ''
  const codeB = selectedPair ? submissions.find(s => s.id === selectedPair.idB)?.code || '' : ''
  const fileA = selectedPair ? submissions.find(s => s.id === selectedPair.idA)?.file : ''
  const fileB = selectedPair ? submissions.find(s => s.id === selectedPair.idB)?.file : ''

  return (
    <div style={{ padding: '40px 80px 80px', maxWidth: 1280, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <Label style={{ marginBottom: 8 }}>Cross-submission analysis</Label>
        <h1 style={{ fontSize: 40, fontWeight: 700, letterSpacing: '-0.02em', color: '#F8FAFC', margin: 0, lineHeight: 1.1 }}>
          Submission similarity
        </h1>
        <p style={{ fontSize: 15, color: '#94A3B8', marginTop: 12, marginBottom: 0, maxWidth: 640 }}>
          Klikni na ćeliju heatmape za prikaz i usporedbu dvaju kodova.
          Visoka sličnost može upućivati na korištenje istog AI prompta.
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
          <div style={{ display: 'flex', gap: 10 }}>
            <Icon name="alert" size={16} color="#EF4444"/>
            <span style={{ color: '#EF4444', fontSize: 14 }}>{error}</span>
          </div>
        </Card>
      )}

      {result && (
        <>
          {/* Heatmap + filter */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 24, alignItems: 'start', marginBottom: 32 }}>
            <Card style={{ padding: 24 }}>
              <Label style={{ marginBottom: 16 }}>Similarity matrix — klikni ćeliju za usporedbu</Label>
              <Heatmap
                ids={result.ids}
                data={result.matrix}
                onSelectPair={handleSelectPair}
              />
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
                <Button variant="secondary" size="sm" icon="upload" onClick={() => { setResult(null); setFiles([]); setSelectedPair(null) }} style={{ width: '100%' }}>
                  Re-upload
                </Button>
              </div>
            </Card>
          </div>

          {/* ── Usporedba kodova (prikazuje se kad kliknemo na ćeliju) ── */}
          {selectedPair && (
            <div ref={compareRef} style={{ marginBottom: 40, animation: 'fadeIn .25s ease' }}>
              <Card style={{ padding: 24 }}>
                {/* Header usporedbe */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <Label style={{ marginBottom: 0 }}>Code comparison</Label>
                    <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#94A3B8' }}>
                      {selectedPair.idA} ↔ {selectedPair.idB}
                    </span>
                    <span style={{
                      fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 700,
                      color: selectedPair.similarity >= 80 ? '#EF4444' : selectedPair.similarity >= 60 ? '#F59E0B' : '#10B981',
                    }}>
                      {selectedPair.similarity}% similar
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedPair(null)}
                    style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#64748B', fontSize: 18, lineHeight: 1 }}>
                    ✕
                  </button>
                </div>

                {/* Dva editora side by side */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#00D4FF', display: 'inline-block' }}/>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#CBD5E1', fontWeight: 600 }}>
                        {selectedPair.idA}
                      </span>
                      <span style={{ fontSize: 11, color: '#64748B' }}>{fileA}</span>
                    </div>
                    <CodeEditor
                      code={codeA}
                      readOnly
                      lang="C"
                      filename={fileA}
                      height={440}
                      annotations={[]}
                    />
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#F59E0B', display: 'inline-block' }}/>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#CBD5E1', fontWeight: 600 }}>
                        {selectedPair.idB}
                      </span>
                      <span style={{ fontSize: 11, color: '#64748B' }}>{fileB}</span>
                    </div>
                    <CodeEditor
                      code={codeB}
                      readOnly
                      lang="C"
                      filename={fileB}
                      height={440}
                      annotations={[]}
                    />
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Suspicious pairs lista */}
          <div>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 18 }}>
              <h2 style={{ fontSize: 24, fontWeight: 600, color: '#F8FAFC', margin: 0, letterSpacing: '-0.01em' }}>Suspicious pairs</h2>
              <span style={{ fontSize: 12, color: '#64748B' }}>{suspiciousPairs.length} pairs above {Math.round(threshold * 100)}%</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {suspiciousPairs.map((p, i) => (
                <div key={i} onClick={() => {
                  const idxA = result.ids.indexOf(p.id_a)
                  const idxB = result.ids.indexOf(p.id_b)
                  handleSelectPair({ i: idxA, j: idxB, idA: p.id_a, idB: p.id_b, similarity: Math.round(p.similarity * 100) })
                }} style={{ cursor: 'pointer' }}>
                  <SuspiciousPair a={p.id_a} b={p.id_b} similarity={Math.round(p.similarity * 100)}/>
                </div>
              ))}
              {suspiciousPairs.length === 0 && (
                <Card style={{ padding: 40, textAlign: 'center' }}>
                  <Icon name="check" size={32} color="#10B981"/>
                  <div style={{ fontSize: 14, color: '#94A3B8', marginTop: 10 }}>
                    No pairs exceed the {Math.round(threshold * 100)}% threshold
                  </div>
                </Card>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
