import { useState } from 'react'
import { Badge, LangBadge, Icon } from './primitives'

function cellStyle(i, hover, first) {
  return {
    padding: '14px 18px', fontSize: 13,
    borderBottom: '1px solid rgba(148,163,184,0.08)',
    background: hover ? 'rgba(0,212,255,0.04)' : i % 2 === 1 ? '#131B2E' : 'transparent',
    boxShadow: hover && first ? 'inset 2px 0 0 #00D4FF' : 'none',
    transition: 'background .12s cubic-bezier(0.22,1,0.36,1)',
  }
}

export default function ResultsTable({ rows, onOpen }) {
  const [sortKey, setSortKey] = useState('ai_probability')
  const [sortDir, setSortDir] = useState('desc')
  const [hover, setHover] = useState(null)

  const sorted = [...rows].sort((a, b) => {
    const dir = sortDir === 'asc' ? 1 : -1
    if (a[sortKey] < b[sortKey]) return -dir
    if (a[sortKey] > b[sortKey]) return dir
    return 0
  })

  const toggle = (k) => {
    if (sortKey === k) setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    else { setSortKey(k); setSortDir('desc') }
  }

  const Th = ({ k, children, style }) => (
    <th onClick={() => toggle(k)} style={{
      fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em',
      fontWeight: 500, color: sortKey === k ? '#00D4FF' : '#94A3B8',
      textAlign: 'left', padding: '14px 18px', background: '#0F1729',
      borderBottom: '1px solid rgba(148,163,184,0.12)',
      cursor: 'pointer', userSelect: 'none', ...style,
    }}>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        {children}
        {sortKey === k && <span style={{ fontSize: 9 }}>{sortDir === 'asc' ? '▲' : '▼'}</span>}
      </span>
    </th>
  )

  return (
    <div style={{
      background: 'rgba(17,24,39,0.6)', border: '1px solid rgba(148,163,184,0.12)',
      borderRadius: 12, overflow: 'hidden', backdropFilter: 'blur(20px)',
      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.03)',
    }}>
      <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
        <thead>
          <tr>
            <Th k="id">Student ID</Th>
            <Th k="file">File</Th>
            <Th k="detected_language">Language</Th>
            <Th k="ai_probability">AI Probability</Th>
            <Th k="verdict">Verdict</Th>
            <th style={{ background: '#0F1729', borderBottom: '1px solid rgba(148,163,184,0.12)', padding: '14px 18px' }}/>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => {
            const prob = Math.round((r.ai_probability || 0) * 100)
            const tone = prob >= 70 ? 'red' : prob >= 40 ? 'amber' : 'green'
            const label = prob >= 70 ? 'LIKELY AI' : prob >= 40 ? 'POSSIBLY AI' : 'LIKELY HUMAN'
            const probColor = prob >= 70 ? '#EF4444' : prob >= 40 ? '#F59E0B' : '#10B981'
            const isHover = hover === i
            return (
              <tr key={r.id || i}
                onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
                onClick={() => onOpen && onOpen(r)} style={{ cursor: 'pointer' }}>
                <td style={cellStyle(i, isHover, true)}>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#F8FAFC' }}>{r.id}</span>
                </td>
                <td style={cellStyle(i, isHover)}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <Icon name="fileCode" size={14} color="#64748B"/>
                    <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#CBD5E1' }}>{r.file || '—'}</span>
                  </span>
                </td>
                <td style={cellStyle(i, isHover)}>
                  <LangBadge lang={r.detected_language ? (r.detected_language.charAt(0).toUpperCase() + r.detected_language.slice(1)) : 'Unknown'}/>
                </td>
                <td style={cellStyle(i, isHover)}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 80, height: 4, background: 'rgba(148,163,184,0.10)', borderRadius: 2, overflow: 'hidden' }}>
                      <div style={{ width: `${prob}%`, height: '100%', background: probColor }}/>
                    </div>
                    <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 700, color: probColor, fontVariantNumeric: 'tabular-nums', minWidth: 36 }}>{prob}%</span>
                  </div>
                </td>
                <td style={cellStyle(i, isHover)}><Badge tone={tone}>{label}</Badge></td>
                <td style={cellStyle(i, isHover)}>
                  <button onClick={e => { e.stopPropagation(); onOpen && onOpen(r) }}
                    style={{
                      background: 'transparent', border: 'none', cursor: 'pointer',
                      color: isHover ? '#00D4FF' : '#64748B',
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      fontSize: 12, fontWeight: 500, padding: 6,
                    }}>
                    <Icon name="eye" size={14}/>
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
