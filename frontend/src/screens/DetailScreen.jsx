import { Button, Card, Badge, Label, Icon, LangBadge } from '../components/primitives'
import CodeEditor from '../components/CodeEditor'
import ResultGauge from '../components/ResultGauge'
import DetailSidebar from '../components/DetailSidebar'
import ExplanationPanel from '../components/ExplanationPanel'

function buildFeatures(allFeatures) {
  if (!allFeatures) return []

  const styleKeys = ['avg_identifier_length', 'avg_function_name_length', 'single_char_name_ratio', 'naming_consistency', 'comment_ratio', 'num_docstrings', 'lexical_diversity', 'trailing_whitespace_ratio']
  const structKeys = ['num_functions', 'avg_function_length', 'max_nesting_depth', 'cyclomatic_complexity_approx', 'if_density', 'for_density', 'ast_depth']
  const statKeys = ['char_entropy', 'token_entropy', 'perplexity']

  const toFeature = (key, category) => {
    const val = allFeatures[key]
    if (val === undefined || val === null) return null
    const fmtVal = typeof val === 'number'
      ? (key.includes('ratio') || key.includes('density') ? (val * 100).toFixed(1) + '%' : val.toFixed ? val.toFixed(2) : String(val))
      : String(val)
    const severity = key.includes('length') && val > 6 ? 'high'
      : key === 'naming_consistency' && val > 0.7 ? 'high'
      : key === 'comment_ratio' && val > 0.2 ? 'high'
      : key.includes('entropy') ? 'medium'
      : 'low'
    return { name: key.replace(/_/g, ' '), value: fmtVal, severity, category }
  }

  return [
    ...styleKeys.map(k => toFeature(k, 'Style')),
    ...structKeys.map(k => toFeature(k, 'Structure')),
    ...statKeys.map(k => toFeature(k, 'Statistical')),
  ].filter(Boolean)
}

function buildAnnotations(topFeatures) {
  if (!topFeatures?.length) return []
  return topFeatures.slice(0, 2).map((f, i) => ({
    line: (i + 1) * 2,
    tone: f.importance > 0.06 ? 'red' : 'amber',
    note: `Suspicious: ${f.name.replace(/_/g, ' ')}`,
  }))
}

export default function DetailScreen({ row, onBack }) {
  if (!row) return null

  const prob = Math.round((row.ai_probability || 0) * 100)
  const tone = prob >= 70 ? 'red' : prob >= 40 ? 'amber' : 'green'
  const label = prob >= 70 ? 'LIKELY AI' : prob >= 40 ? 'POSSIBLY AI' : 'LIKELY HUMAN'
  const lang = row.detected_language || 'python'
  const langDisplay = lang.charAt(0).toUpperCase() + lang.slice(1)

  const features = buildFeatures(row.all_features)
  const annotations = buildAnnotations(row.top_features)
  const code = row.code || '// Code not available'

  return (
    <div style={{ padding: '32px 80px 80px', maxWidth: 1280, margin: '0 auto' }}>
      <button onClick={onBack} style={{
        background: 'transparent', border: 'none', color: '#94A3B8', cursor: 'pointer',
        display: 'inline-flex', alignItems: 'center', gap: 6, padding: 0, marginBottom: 20, fontSize: 13,
      }}>
        <Icon name="arrowLeft" size={14}/> Back to batch
      </button>

      {/* Header */}
      <Card style={{ marginBottom: 24, padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 32 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
              <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 24, fontWeight: 700, color: '#F8FAFC' }}>{row.id}</span>
              <LangBadge lang={langDisplay}/>
              <Badge tone={tone}>{label}</Badge>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#94A3B8', fontSize: 13 }}>
              <Icon name="fileCode" size={14}/>
              <span style={{ fontFamily: 'JetBrains Mono, monospace' }}>{row.file || row.id}</span>
            </div>
          </div>
          <ResultGauge value={prob} size={140} animate={false}/>
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 24, alignItems: 'start' }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <Label style={{ marginBottom: 0 }}>Annotated source</Label>
            {annotations.length > 0 && (
              <span style={{ fontSize: 11, color: '#64748B' }}>{annotations.length} suspicious lines flagged</span>
            )}
          </div>
          <CodeEditor code={code} readOnly lang={langDisplay} height={420} annotations={annotations} filename={row.file}/>

          <ExplanationPanel
            explanations={row.explanations}
            verdict={row.verdict}
            aiProbability={row.ai_probability}
          />
        </div>

        <DetailSidebar features={features}/>
      </div>
    </div>
  )
}
