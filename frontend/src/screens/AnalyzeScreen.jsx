import { useState } from 'react'
import { Button, Card, Label, Icon, Spinner, LangBadge } from '../components/primitives'
import CodeEditor from '../components/CodeEditor'
import ResultGauge from '../components/ResultGauge'
import { FeatureCard } from '../components/FeatureCard'
import { analyzeCode } from '../api/client'
import ExplanationPanel from '../components/ExplanationPanel'

const SAMPLE = `def calculate_factorial_recursive(number_to_compute):
    """Calculate factorial using recursive approach with input validation."""
    if not isinstance(number_to_compute, int):
        raise TypeError("Input must be an integer value")
    if number_to_compute < 0:
        raise ValueError("Factorial undefined for negative numbers")
    if number_to_compute <= 1:
        return 1
    return number_to_compute * calculate_factorial_recursive(number_to_compute - 1)


def main_execution_function():
    """Main entry point for the factorial computation program."""
    user_input_value = 10
    final_result = calculate_factorial_recursive(user_input_value)
    print(f"The factorial of {user_input_value} is {final_result}")


if __name__ == "__main__":
    main_execution_function()`

function severityFor(key, value) {
  const highKeys = ['avg_identifier_length', 'avg_function_name_length', 'naming_consistency', 'comment_ratio', 'num_docstrings']
  const medKeys  = ['token_entropy', 'char_entropy', 'cyclomatic_complexity_approx', 'avg_function_length']
  if (highKeys.includes(key)) return value > 5 ? 'high' : 'medium'
  if (medKeys.includes(key)) return 'medium'
  return 'low'
}

function formatFeatureVal(key, val) {
  if (typeof val === 'number') {
    if (key.includes('ratio') || key.includes('density')) return (val * 100).toFixed(1) + '%'
    if (key.includes('entropy')) return val.toFixed(2)
    if (Number.isInteger(val)) return String(val)
    return val.toFixed(2)
  }
  return String(val)
}

const FEATURE_LABELS = {
  avg_identifier_length:    { label: 'Avg. identifier length', icon: 'code' },
  naming_consistency:       { label: 'Naming consistency', icon: 'sparkles' },
  comment_ratio:            { label: 'Comment density', icon: 'fileCode' },
  token_entropy:            { label: 'Token entropy', icon: 'chart' },
  cyclomatic_complexity_approx: { label: 'Avg. complexity', icon: 'chart' },
  avg_function_length:      { label: 'Avg. function length', icon: 'code' },
}

export default function AnalyzeScreen() {
  const [code, setCode] = useState(SAMPLE)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const run = async () => {
    if (!code.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const data = await analyzeCode(code)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const topFeatures = result ? Object.entries(FEATURE_LABELS).map(([key, meta]) => ({
    name: meta.label,
    icon: meta.icon,
    value: formatFeatureVal(key, result.all_features?.[key] ?? 0),
    severity: severityFor(key, result.all_features?.[key] ?? 0),
  })) : []

  const lang = result?.detected_language
  const langDisplay = lang ? lang.charAt(0).toUpperCase() + lang.slice(1) : 'Python'

  return (
    <div>
      {/* Hero */}
      <section style={{ padding: '80px 80px 48px', textAlign: 'center', position: 'relative' }}>
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: 'linear-gradient(to right, rgba(148,163,184,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.04) 1px, transparent 1px)',
          backgroundSize: '32px 32px', pointerEvents: 'none',
          maskImage: 'radial-gradient(ellipse at center, black 30%, transparent 70%)',
        }}/>
        <div style={{ position: 'relative' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '6px 14px', borderRadius: 999,
            background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.20)',
            marginBottom: 24,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D4FF', boxShadow: '0 0 8px #00D4FF' }}/>
            <span style={{ fontSize: 12, color: '#00D4FF', fontWeight: 500, letterSpacing: '0.04em' }}>v1.0 · 42 statistical signals</span>
          </div>
          <h1 style={{ fontSize: 56, fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.05, color: '#F8FAFC', margin: '0 0 20px', maxWidth: 800, marginLeft: 'auto', marginRight: 'auto' }}>
            Detect <span style={{ color: '#00D4FF' }}>AI-generated</span> code instantly
          </h1>
          <p style={{ fontSize: 18, color: '#94A3B8', lineHeight: 1.55, maxWidth: 600, margin: '0 auto 32px' }}>
            CodeSentinel analyzes 42 statistical signals — identifier patterns, comment density, structural rhythm — to estimate the probability that a submission was written by a large language model.
          </p>
          <Button variant="primary" size="lg" icon="play" onClick={() => document.getElementById('analyzer')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>
            Start analyzing
          </Button>
        </div>
      </section>

      {/* Analyzer */}
      <section id="analyzer" style={{ padding: '24px 80px 80px', maxWidth: 1280, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 24, marginBottom: 32 }}>
          <div>
            <Label style={{ marginBottom: 10 }}>Paste or edit code</Label>
            <CodeEditor code={code} onChange={setCode} lang={langDisplay} height={380}/>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
              <div style={{ fontSize: 12, color: '#64748B', fontFamily: 'JetBrains Mono, monospace' }}>
                {code.split('\n').length} lines · {code.length} chars
              </div>
              <Button variant="primary" icon="play" onClick={run} disabled={loading || !code.trim()}>
                {loading ? 'Analyzing…' : 'Analyze code'}
              </Button>
            </div>
          </div>

          <Card glow style={{ padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 340 }}>
            {loading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
                <Spinner size={40}/>
                <div style={{ fontSize: 13, color: '#94A3B8', letterSpacing: '0.04em', textTransform: 'uppercase' }}>Analyzing…</div>
              </div>
            ) : error ? (
              <div style={{ textAlign: 'center', padding: 20 }}>
                <Icon name="alert" size={32} color="#EF4444"/>
                <div style={{ fontSize: 13, color: '#EF4444', marginTop: 12 }}>{error}</div>
                <div style={{ fontSize: 11, color: '#64748B', marginTop: 6 }}>Make sure the Flask server is running</div>
              </div>
            ) : result ? (
              <ResultGauge value={Math.round(result.ai_probability * 100)} size={200}/>
            ) : (
              <div style={{ padding: 40, textAlign: 'center' }}>
                <Icon name="sparkles" size={32} color="#475569"/>
                <div style={{ fontSize: 14, color: '#64748B', marginTop: 14 }}>Run an analysis to see results</div>
              </div>
            )}
          </Card>
        </div>

        {result && (
          <div style={{ animation: 'fadeIn .3s ease' }}>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 18 }}>
              <h2 style={{ fontSize: 24, fontWeight: 600, color: '#F8FAFC', margin: 0, letterSpacing: '-0.01em' }}>Feature breakdown</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <LangBadge lang={langDisplay}/>
                <span style={{ fontSize: 12, color: '#64748B' }}>Top 6 of 42 signals · sorted by suspicion</span>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
              {topFeatures.map((f, i) => <FeatureCard key={i} {...f}/>)}
            </div>

            {result.top_features?.length > 0 && (
              <Card style={{ padding: 24 }}>
                <Label style={{ marginBottom: 16 }}>Key signals</Label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {result.top_features.map((f, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: 13, color: '#CBD5E1' }}>{f.name.replace(/_/g, ' ')}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ width: 80, height: 3, background: 'rgba(148,163,184,0.10)', borderRadius: 2, overflow: 'hidden' }}>
                          <div style={{ width: `${Math.round(f.importance * 1000)}%`, height: '100%', background: '#00D4FF' }}/>
                        </div>
                        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#94A3B8', minWidth: 40, textAlign: 'right' }}>
                          {f.value}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Explanations panel */}
            <ExplanationPanel
              explanations={result.explanations}
              verdict={result.verdict}
              aiProbability={result.ai_probability}
            />
          </div>
        )}
      </section>
    </div>
  )
}
