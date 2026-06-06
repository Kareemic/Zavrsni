import { useState } from 'react'
import { Button, Card, Label, Icon, Input } from '../components/primitives'
import Dropzone from '../components/Dropzone'
import ResultsTable from '../components/ResultsTable'
import { StatCard } from '../components/FeatureCard'
import { analyzeBatch } from '../api/client'

export default function BatchScreen({ onOpenRow }) {
  const [files,    setFiles]   = useState([])
  const [results,  setResults] = useState([])
  const [summary,  setSummary] = useState(null)
  const [loading,  setLoading] = useState(false)
  const [progress, setProgress] = useState(0)       // 0-100
  const [done,     setDone]    = useState(0)        // koliko fajlova završilo
  const [error,    setError]   = useState(null)
  const [search,   setSearch]  = useState('')

  const handleFiles = (fileList) => {
    const arr = Array.from(fileList)
    setFiles(arr); setResults([]); setSummary(null); setError(null); setProgress(0); setDone(0)
  }

  const runBatch = async () => {
    if (!files.length) return
    setLoading(true); setError(null); setResults([]); setSummary(null); setProgress(0); setDone(0)

    // Učitamo sve fajlove unaprijed da znamo kod za svaki
    const submissions = await Promise.all(files.map(async (f) => ({
      id:   f.name.replace(/\.[^.]+$/, ''),
      file: f.name,
      code: await f.text(),
    })))

    try {
      // Streaming — onResult se zove za svaki fajl čim stigne s backenda
      const finalSummary = await analyzeBatch(
        submissions,

        // Callback za svaki gotov rezultat — odmah ga dodajemo u tablicu
        (result, index, total) => {
          const sub = submissions[index - 1]
          const enriched = {
            ...result,
            file: sub?.file || result.id,
            code: sub?.code || '',
          }
          setResults(prev => [...prev, enriched])
          setDone(index)
        },

        // Callback za napredak (0-100%)
        (pct) => setProgress(pct),
      )

      setSummary(finalSummary)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const exportCSV = () => {
    if (!results.length) return

    const headers = ['ID', 'Datoteka', 'Jezik', 'AI vjerojatnost (%)', 'Zakljucak']
    const keys    = ['id', 'file', 'detected_language', 'ai_probability', 'verdict']

    const escapeCell = (val) => {
      const s = String(val ?? '')
      if (s.includes(';') || s.includes('"') || s.includes('\n')) {
        return '"' + s.replace(/"/g, '""') + '"'
      }
      return s
    }

    const rows = results.map(r => keys.map(h => {
      if (h === 'ai_probability') return escapeCell(Math.round((r[h] || 0) * 100) + '%')
      return escapeCell(r[h] || '')
    }))

    const sep = ';'
    const csvContent = [
      headers.map(escapeCell).join(sep),
      ...rows.map(r => r.join(sep)),
    ].join('\r\n')

    const BOM = '\uFEFF'
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(blob),
      download: 'codesentinel_rezultati.csv',
    })
    a.click()
  }

  const filtered = results.filter(r =>
    !search || r.id?.toLowerCase().includes(search.toLowerCase()) || r.file?.toLowerCase().includes(search.toLowerCase())
  )

  const total = files.length

  return (
    <div style={{ padding: '40px 80px 80px', maxWidth: 1280, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <Label style={{ marginBottom: 8 }}>Batch analysis</Label>
        <h1 style={{ fontSize: 40, fontWeight: 700, letterSpacing: '-0.02em', color: '#F8FAFC', margin: 0, lineHeight: 1.1 }}>
          Class overview
        </h1>
        <p style={{ fontSize: 15, color: '#94A3B8', marginTop: 12, marginBottom: 0, maxWidth: 600 }}>
          Rezultati se prikazuju u realnom vremenu čim svaki fajl bude analiziran.
        </p>
      </div>

      {/* Upload zona — prikazuje se samo na početku */}
      {!loading && !results.length && !summary && (
        <div style={{ marginBottom: 24 }}>
          <Dropzone files={files} onUpload={handleFiles}/>
          {files.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
              <Button variant="primary" icon="play" onClick={runBatch}>
                Analyze {files.length} submission{files.length !== 1 ? 's' : ''}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Progress bar — prikazuje se za vrijeme analize */}
      {loading && (
        <Card style={{ padding: 24, marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#00D4FF', boxShadow: '0 0 8px #00D4FF', animation: 'pulse 1s ease infinite' }}/>
              <span style={{ fontSize: 14, color: '#CBD5E1' }}>
                Analyzing… <strong style={{ color: '#F8FAFC', fontFamily: 'JetBrains Mono, monospace' }}>{done}</strong> / {total} files
              </span>
            </div>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, color: '#00D4FF', fontWeight: 700 }}>
              {progress}%
            </span>
          </div>
          {/* Progress bar */}
          <div style={{ height: 6, background: 'rgba(148,163,184,0.10)', borderRadius: 3, overflow: 'hidden' }}>
            <div style={{
              width: `${progress}%`, height: '100%',
              background: 'linear-gradient(90deg, #00D4FF, #06B6D4)',
              borderRadius: 3,
              transition: 'width .3s cubic-bezier(0.22,1,0.36,1)',
              boxShadow: '0 0 8px rgba(0,212,255,0.4)',
            }}/>
          </div>
          {/* Tablica se popunjava ispod progress bara u realnom vremenu */}
          {results.length > 0 && (
            <div style={{ marginTop: 8, fontSize: 12, color: '#64748B' }}>
              {results.length} result{results.length !== 1 ? 's' : ''} so far — scroll down to see them
            </div>
          )}
        </Card>
      )}

      {error && (
        <Card style={{ padding: 20, marginBottom: 24, borderColor: 'rgba(239,68,68,0.35)', background: 'rgba(239,68,68,0.06)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Icon name="alert" size={16} color="#EF4444"/>
            <span style={{ fontSize: 14, color: '#EF4444' }}>{error}</span>
          </div>
        </Card>
      )}

      {/* Rezultati — prikazuju se čim prvi stignu, i rastu za vrijeme analize */}
      {results.length > 0 && (
        <>
          {/* Stat kartice — vidljive tek kad je sve gotovo */}
          {summary && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
              <StatCard label="Total submissions" value={summary.total} delta="files analyzed" icon="users" iconColor="#00D4FF"/>
              <StatCard label="High risk" value={summary.high_risk} delta="≥ 70% AI probability" deltaColor="#EF4444" icon="alert" iconColor="#EF4444"/>
              <StatCard label="Medium risk" value={summary.medium_risk} delta="40–69% probability" deltaColor="#F59E0B" icon="alert" iconColor="#F59E0B"/>
              <StatCard label="Low risk" value={summary.low_risk} delta="< 40% probability" deltaColor="#10B981" icon="check" iconColor="#10B981"/>
            </div>
          )}

          {/* Action bar */}
          <div style={{ marginBottom: 16, padding: '12px 18px', background: summary ? 'rgba(16,185,129,0.06)' : 'rgba(0,212,255,0.04)', border: `1px solid ${summary ? 'rgba(16,185,129,0.20)' : 'rgba(0,212,255,0.15)'}`, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Icon name={summary ? 'check' : 'chart'} size={16} color={summary ? '#10B981' : '#00D4FF'}/>
              <span style={{ fontSize: 13, color: '#CBD5E1' }}>
                {summary
                  ? <><strong style={{ color: '#F8FAFC' }}>{summary.total} files</strong> analyzed — avg. AI probability: <strong style={{ color: '#F8FAFC' }}>{Math.round((summary.avg_ai_probability || 0) * 100)}%</ strong></>
                  : <><strong style={{ color: '#F8FAFC' }}>{results.length}</strong> of {total} analyzed…</>
                }
              </span>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {summary && (
                <>
                  <Button variant="secondary" size="sm" icon="upload" onClick={() => { setResults([]); setSummary(null); setFiles([]); setProgress(0); setDone(0) }}>
                    Re-upload
                  </Button>
                  <Button variant="primary" size="sm" icon="download" onClick={exportCSV}>
                    Export CSV
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Search */}
          <div style={{ marginBottom: 16 }}>
            <Input icon="search" placeholder="Search by student ID or filename…" value={search} onChange={setSearch} style={{ width: 320 }}/>
          </div>

          <ResultsTable rows={filtered} onOpen={onOpenRow}/>
        </>
      )}
    </div>
  )
}
