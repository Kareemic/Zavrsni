import { LangBadge } from './primitives'

function SyntaxTinted({ code }) {
  const tokens = code.split(/(\b(?:def|return|if|else|elif|for|while|import|from|class|in|not|and|or|True|False|None|self|function|const|let|var|=>|public|private|static|void|int|string|bool)\b|"[^"]*"|'[^']*'|`[^`]*`|#[^\n]*|\/\/[^\n]*|\/\*[\s\S]*?\*\/|\b\d+\b)/g)
  return tokens.map((t, i) => {
    if (/^(def|return|if|else|elif|for|while|import|from|class|in|not|and|or|True|False|None|self|function|const|let|var|public|private|static|void|int|string|bool)$/.test(t))
      return <span key={i} style={{ color: '#22E0FF' }}>{t}</span>
    if (/^["'`].*["'`]$/.test(t)) return <span key={i} style={{ color: '#10B981' }}>{t}</span>
    if (/^(#|\/\/)/.test(t)) return <span key={i} style={{ color: '#64748B', fontStyle: 'italic' }}>{t}</span>
    if (/^\d+$/.test(t)) return <span key={i} style={{ color: '#F59E0B' }}>{t}</span>
    return <span key={i}>{t}</span>
  })
}

export default function CodeEditor({ code, onChange, lang = 'Python', readOnly = false, height = 360, annotations = [], filename }) {
  const lines = (code || '').split('\n')
  const displayName = filename || 'submission.' + (lang === 'Python' ? 'py' : lang === 'Java' ? 'java' : lang === 'JavaScript' ? 'js' : 'txt')

  return (
    <div style={{
      background: '#0F172A', border: '1px solid rgba(148,163,184,0.12)',
      borderRadius: 10, overflow: 'hidden', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.03)',
    }}>
      {/* Header bar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 14px', borderBottom: '1px solid rgba(148,163,184,0.12)',
        background: 'rgba(15,23,41,0.6)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ display: 'flex', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#EF4444', opacity: 0.6 }}/>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#F59E0B', opacity: 0.6 }}/>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#10B981', opacity: 0.6 }}/>
          </div>
          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#94A3B8' }}>{displayName}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {!readOnly && <span style={{ fontSize: 10, color: '#64748B', letterSpacing: '0.04em', textTransform: 'uppercase' }}>Auto-detected</span>}
          <LangBadge lang={lang}/>
        </div>
      </div>

      {/* Editor body */}
      <div style={{ display: 'flex', height, position: 'relative', overflow: 'hidden' }}>
        {/* Line numbers */}
        <div style={{
          padding: '12px 12px 12px 16px', background: 'rgba(10,15,28,0.4)',
          fontFamily: 'JetBrains Mono, monospace', fontSize: 12, lineHeight: 1.7,
          color: '#475569', textAlign: 'right', userSelect: 'none',
          borderRight: '1px solid rgba(148,163,184,0.08)', minWidth: 44,
          overflowY: 'hidden',
        }}>
          {lines.map((_, i) => {
            const ann = annotations.find(a => a.line === i + 1)
            return (
              <div key={i} style={{
                color: ann ? (ann.tone === 'red' ? '#EF4444' : '#F59E0B') : '#475569',
                fontWeight: ann ? 600 : 400,
              }}>{i + 1}</div>
            )
          })}
        </div>

        {/* Code area */}
        <div style={{ flex: 1, position: 'relative', overflow: 'auto' }}>
          {annotations.map((a, i) => (
            <div key={i} style={{
              position: 'absolute', left: 0, right: 0,
              top: `calc(12px + ${a.line - 1} * 1.7em)`, height: '1.7em',
              background: a.tone === 'red' ? 'rgba(239,68,68,0.08)' : 'rgba(245,158,11,0.08)',
              borderLeft: `2px solid ${a.tone === 'red' ? '#EF4444' : '#F59E0B'}`,
              pointerEvents: 'none', zIndex: 1,
            }}>
              {a.note && (
                <span style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  fontSize: 10, color: a.tone === 'red' ? '#EF4444' : '#F59E0B',
                  fontFamily: 'Inter, sans-serif', background: a.tone === 'red' ? 'rgba(239,68,68,0.12)' : 'rgba(245,158,11,0.12)',
                  padding: '2px 6px', borderRadius: 4,
                }}>⚠ {a.note}</span>
              )}
            </div>
          ))}
          {readOnly ? (
            <pre style={{
              margin: 0, padding: '12px 16px',
              fontFamily: 'JetBrains Mono, monospace', fontSize: 12, lineHeight: 1.7,
              color: '#CBD5E1', whiteSpace: 'pre', overflow: 'visible',
            }}><SyntaxTinted code={code}/></pre>
          ) : (
            <textarea value={code} onChange={e => onChange && onChange(e.target.value)}
              spellCheck="false" placeholder="Paste your code here…"
              style={{
                width: '100%', height: '100%', border: 'none', outline: 'none', resize: 'none',
                background: 'transparent', color: '#CBD5E1',
                fontFamily: 'JetBrains Mono, monospace', fontSize: 12, lineHeight: 1.7,
                padding: '12px 16px',
              }}/>
          )}
        </div>
      </div>
    </div>
  )
}
