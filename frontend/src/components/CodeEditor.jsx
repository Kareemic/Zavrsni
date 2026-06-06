import { useRef } from 'react'
import { LangBadge } from './primitives'

// Osnovna syntax tinting za čitljivost (nije full highlighter)
function SyntaxTinted({ code }) {
  const tokens = code.split(
    /(\b(?:def|return|if|else|elif|for|while|import|from|class|in|not|and|or|True|False|None|self|function|const|let|var|public|private|static|void|int|string|bool|unsigned|include|struct|typedef)\b|"[^"]*"|'[^']*'|`[^`]*`|\/\/[^\n]*|#[^\n]*|\b\d+\b)/g
  )
  return tokens.map((t, i) => {
    if (/^(def|return|if|else|elif|for|while|import|from|class|in|not|and|or|True|False|None|self|function|const|let|var|public|private|static|void|int|string|bool|unsigned|struct|typedef)$/.test(t))
      return <span key={i} style={{ color: '#22E0FF' }}>{t}</span>
    if (/^["'`].*["'`]$/.test(t))
      return <span key={i} style={{ color: '#10B981' }}>{t}</span>
    if (/^(#|\/\/)/.test(t))
      return <span key={i} style={{ color: '#64748B', fontStyle: 'italic' }}>{t}</span>
    if (/^\d+$/.test(t))
      return <span key={i} style={{ color: '#F59E0B' }}>{t}</span>
    return <span key={i}>{t}</span>
  })
}

export default function CodeEditor({
  code,
  onChange,
  lang = 'Python',
  readOnly = false,
  height = 360,
  annotations = [],
  filename,
}) {
  const scrollRef = useRef(null)
  const lines = (code || '').split('\n')
  const displayName = filename || ('submission.' + (
    lang === 'Python' ? 'py' :
    lang === 'Java'   ? 'java' :
    lang === 'JavaScript' ? 'js' :
    lang === 'C++'    ? 'cpp' :
    lang === 'C'      ? 'c' : 'txt'
  ))

  // Mapa linija na anotacije za brzo traženje
  const annotMap = {}
  for (const a of annotations) {
    annotMap[a.line] = a
  }

  return (
    <div style={{
      background: '#0F172A',
      border: '1px solid rgba(148,163,184,0.12)',
      borderRadius: 10,
      overflow: 'hidden',
      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.03)',
    }}>

      {/* ── Header ── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 14px',
        borderBottom: '1px solid rgba(148,163,184,0.12)',
        background: 'rgba(15,23,41,0.6)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ display: 'flex', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#EF4444', opacity: 0.6 }}/>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#F59E0B', opacity: 0.6 }}/>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#10B981', opacity: 0.6 }}/>
          </div>
          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#94A3B8' }}>
            {displayName}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {annotations.length > 0 && (
            <span style={{
              fontSize: 10, color: '#F59E0B', letterSpacing: '0.04em',
              background: 'rgba(245,158,11,0.10)', border: '1px solid rgba(245,158,11,0.25)',
              padding: '2px 8px', borderRadius: 4,
            }}>
              {annotations.filter(a => a.tone === 'red').length} strong ·{' '}
              {annotations.filter(a => a.tone === 'amber').length} moderate
            </span>
          )}
          <LangBadge lang={lang}/>
        </div>
      </div>

      {/* ── Editor tijelo ──
           Jedan scroll container koji sadrži i broj linije i kod,
           tako da se uvijek pomiču zajedno.
      */}
      {readOnly ? (
        <div ref={scrollRef} style={{ height, overflow: 'auto' }}>
          <table style={{
            borderCollapse: 'collapse',
            width: '100%',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 12,
            lineHeight: 1.7,
          }}>
            <tbody>
              {lines.map((line, idx) => {
                const lineNum = idx + 1
                const ann = annotMap[lineNum]
                const isRed   = ann?.tone === 'red'
                const isAmber = ann?.tone === 'amber'
                const bgColor = isRed
                  ? 'rgba(239,68,68,0.10)'
                  : isAmber
                  ? 'rgba(245,158,11,0.08)'
                  : 'transparent'
                const borderLeft = isRed
                  ? '2px solid #EF4444'
                  : isAmber
                  ? '2px solid #F59E0B'
                  : '2px solid transparent'

                return (
                  <tr key={idx} title={ann?.note || ''} style={{ background: bgColor }}>

                    {/* Broj linije */}
                    <td style={{
                      width: 44,
                      minWidth: 44,
                      padding: '0 10px 0 16px',
                      textAlign: 'right',
                      color: ann ? (isRed ? '#EF4444' : '#F59E0B') : '#475569',
                      userSelect: 'none',
                      borderRight: '1px solid rgba(148,163,184,0.08)',
                      borderLeft,
                      verticalAlign: 'top',
                      paddingTop: '1px',
                      whiteSpace: 'nowrap',
                    }}>
                      {lineNum}
                    </td>

                    {/* Ikona oznake (samo za označene linije) */}
                    <td style={{
                      width: 20,
                      minWidth: 20,
                      textAlign: 'center',
                      verticalAlign: 'top',
                      paddingTop: '2px',
                      color: isRed ? '#EF4444' : isAmber ? '#F59E0B' : 'transparent',
                      fontSize: 9,
                    }}>
                      {ann ? '⚠' : ''}
                    </td>

                    {/* Kod */}
                    <td style={{
                      padding: '0 16px',
                      color: '#CBD5E1',
                      whiteSpace: 'pre',
                      verticalAlign: 'top',
                    }}>
                      <SyntaxTinted code={line}/>
                    </td>

                    {/* Tooltip poruka (prikazuje se desno ako postoji anotacija) */}
                    {ann && (
                      <td style={{
                        padding: '0 12px',
                        fontSize: 10,
                        color: isRed ? '#EF4444' : '#F59E0B',
                        background: isRed ? 'rgba(239,68,68,0.08)' : 'rgba(245,158,11,0.08)',
                        whiteSpace: 'nowrap',
                        verticalAlign: 'top',
                        maxWidth: 280,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        paddingTop: '2px',
                        fontStyle: 'italic',
                      }}>
                        {ann.note}
                      </td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : (
        // Edit mode — textarea s brojevima linija u sync
        <div style={{ display: 'flex', height, overflow: 'hidden' }}>
          {/* Brojevi linija za edit mode — sinkronizirani scrollom */}
          <div style={{
            padding: '12px 12px 12px 16px',
            background: 'rgba(10,15,28,0.4)',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 12,
            lineHeight: 1.7,
            color: '#475569',
            textAlign: 'right',
            userSelect: 'none',
            borderRight: '1px solid rgba(148,163,184,0.08)',
            minWidth: 44,
            overflowY: 'hidden',
            pointerEvents: 'none',
          }}>
            {lines.map((_, i) => <div key={i}>{i + 1}</div>)}
          </div>
          <textarea
            value={code}
            onChange={e => onChange && onChange(e.target.value)}
            spellCheck="false"
            placeholder="Paste your code here…"
            onScroll={e => {
              // Sinkroniziramo scroll brojeva linija s textarea
              const prev = e.target.previousSibling
              if (prev) prev.scrollTop = e.target.scrollTop
            }}
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              resize: 'none',
              background: 'transparent',
              color: '#CBD5E1',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 12,
              lineHeight: 1.7,
              padding: '12px 16px',
              overflowY: 'auto',
            }}
          />
        </div>
      )}
    </div>
  )
}
