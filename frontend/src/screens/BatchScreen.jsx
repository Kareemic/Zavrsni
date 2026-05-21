import { useState } from 'react'
import { Button, Card, Label, Icon, Spinner, Input } from '../components/primitives'
import Dropzone from '../components/Dropzone'
import ResultsTable from '../components/ResultsTable'
import { StatCard } from '../components/FeatureCard'
import { analyzeBatch } from '../api/client'

export default function BatchScreen({ onOpenRow }) {
  const [files, setFiles] = useState([])
  const [results, setResults] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')

  const handleFiles = (fileList) => {
    const arr = Array.from(fileList)
    setFiles(arr); setResults([]); setSummary(null); setError(null)
  }

  const runBatch = async () => {
    if (!files.length) return
    setLoading(true); setError(null); setProgress(0)

    const submissions = await Promise.all(files.map(async (f) => ({
      id: f.name.replace(/\.[^.]+$/, ''),
      file: f.name,
      code: await f.text(),
    })))

    try {
      const data = await analyzeBatch(submissions)
      const withFile = data.results.map((r, i) => ({ ...r, file: submissions[i]?.file || r.id }))
      setResults(withFile)
      setSummary(data.summary)
      setProgress(100)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const exportCSV = () => {
    if (!results.length) return
    const headers = ['id', 'file', 'detected_language', 'ai_probability', 'verdict']
    const rows = results.map(r => headers.map(h => {
      const v = r[h]
      return typeof v === 'number' ? (h === 'ai_probability' ? Math.round(v * 100) + '%' : v) : (v || '')
    }))
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
    const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(new Blob([csv])), download: 'codesentinel_results.csv' })
    a.click()
  }

  const filtered = results.filter(r =>
    !search || r.id?.toLowerCase().includes(search.toLowerCase()) || r.file?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div style={{ padding: '40px 80px 80px', maxWidth: 1280, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <Label style={{ marginBottom: 8 }}>Batch analysis</Label>
        <h1 style={{ fontSize: 40, fontWeight: 700, letterSpacing: '-0.02em', color: '#F8FAFC', margin: 0, lineHeight: 1.1 }}>
          Class overview
        </h1>
        <p style={{ fontSize: 15, color: '#94A3B8', marginTop: 12, marginBottom: 0, maxWidth: 600 }}>
          Drop a folder of submissions, then sort by AI probability to triage your grading queue.
        </p>
      </div>

      {/* Upload zone */}
      {!results.length && (
        <div style={{ marginBottom: 24 }}>
          <Dropzone files={files} onUpload={handleFiles}/>
          {files.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
              <Button variant="primary" icon="play" onClick={runBatch} disabled={loading}>
                {loading ? 'Analyzing…' : `Analyze ${files.length} file${files.length !== 1 ? 's' : ''}`}
              </Button>
            </div>
          )}
        </div>
      )}

      {loading && (
        <Card style={{ padding: 40, textAlign: 'center', marginBottom: 24 }}>
          <Spinner size={40} style={{ margin: '0 auto 16px' }}/>
          <div style={{ fontSize: 14, color: '#94A3B8' }}>Analyzing {files.length} files…</div>
          <div style={{ width: 240, height: 4, background: 'rgba(148,163,184,0.10)', borderRadius: 2, margin: '16px auto 0', overflow: 'hidden' }}>
            <div style={{ width: '60%', height: '100%', background: '#00D4FF', animation: 'pulse 1.2s ease-in-out infinite' }}/>
          </div>
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

      {summary && (
        <>
          {/* Stat cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
            <StatCard label="Total submissions" value={summary.total} delta="files analyzed" icon="users" iconColor="#00D4FF"/>
            <StatCard label="High risk" value={summary.high_risk} delta="≥ 70% AI probability" deltaColor="#EF4444" icon="alert" iconColor="#EF4444"/>
            <StatCard label="Medium risk" value={summary.medium_risk} delta="40–69% probability" deltaColor="#F59E0B" icon="alert" iconColor="#F59E0B"/>
            <StatCard label="Low risk" value={summary.low_risk} delta="< 40% probability" deltaColor="#10B981" icon="check" iconColor="#10B981"/>
          </div>

          {/* Success bar */}
          <div style={{ marginBottom: 24, padding: '14px 18px', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.20)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Icon name="check" size={16} color="#10B981"/>
              <span style={{ fontSize: 13, color: '#CBD5E1' }}>Analyzed <strong style={{ color: '#F8FAFC' }}>{summary.total} files</strong> — avg. AI probability: <strong style={{ color: '#F8FAFC' }}>{Math.round(summary.avg_ai_probability * 100)}%</strong></span>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button variant="secondary" size="sm" icon="upload" onClick={() => { setResults([]); setSummary(null); setFiles([]) }}>Re-upload</Button>
              <Button variant="primary" size="sm" icon="download" onClick={exportCSV}>Export CSV</Button>
            </div>
          </div>

          {/* Toolbar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <Input icon="search" placeholder="Search by student ID or filename…" value={search} onChange={setSearch} style={{ width: 320 }}/>
          </div>

          <ResultsTable rows={filtered} onOpen={onOpenRow}/>
        </>
      )}
    </div>
  )
}
