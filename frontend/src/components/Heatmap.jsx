import { useState } from 'react'

function colorFor(v) {
  if (v == null) return '#0F1729'
  if (v < 30) {
    const t = v / 30
    return `rgb(${Math.round(15 + t * 10)}, ${Math.round(28 + t * 40)}, ${Math.round(60 + t * 80)})`
  }
  if (v < 60) {
    const t = (v - 30) / 30
    return `rgb(${Math.round(25 + t * (0 - 25))}, ${Math.round(68 + t * (212 - 68))}, ${Math.round(140 + t * (255 - 140))})`
  }
  if (v < 80) {
    const t = (v - 60) / 20
    return `rgb(${Math.round(t * 245)}, ${Math.round(212 + t * (158 - 212))}, ${Math.round(255 + t * (11 - 255))})`
  }
  const t = (v - 80) / 20
  return `rgb(${Math.round(245 + t * (239 - 245))}, ${Math.round(158 + t * (68 - 158))}, ${Math.round(11 + t * (68 - 11))})`
}

export default function Heatmap({ data, ids, onSelectPair }) {
  const [tip, setTip]       = useState(null)
  const [selected, setSelected] = useState(null)   // { i, j }

  if (!data || !ids || ids.length === 0) {
    return <div style={{ padding: 40, textAlign: 'center', color: '#64748B', fontSize: 14 }}>No data.</div>
  }

  const n = ids.length
  const cellSize = Math.max(20, Math.min(80, Math.floor(480 / n)))
  const labelW   = 72
  const showPct  = cellSize >= 36

  const handleClick = (i, j) => {
    if (i === j) return
    const newSel = selected?.i === i && selected?.j === j ? null : { i, j }
    setSelected(newSel)
    if (onSelectPair) {
      onSelectPair(newSel ? { i, j, idA: ids[i], idB: ids[j], similarity: Math.round(data[i][j] * 100) } : null)
    }
  }

  return (
    <div style={{ position: 'relative' }}>
      {n < 3 && (
        <div style={{ marginBottom: 16, padding: '10px 14px', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 8, fontSize: 12, color: '#F59E0B' }}>
          Heatmap je najkorisniji s 3 ili više datoteka.
        </div>
      )}

      <div style={{ overflowX: 'auto' }}>
        {/* Gornji labeli */}
        <div style={{ display: 'flex', marginLeft: labelW }}>
          {ids.map((id, i) => (
            <div key={i} style={{ width: cellSize, flexShrink: 0, height: labelW, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', paddingBottom: 8 }}>
              <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: Math.max(8, Math.min(11, cellSize * 0.35)), color: '#64748B', transform: 'rotate(-45deg)', transformOrigin: 'bottom center', whiteSpace: 'nowrap', display: 'block' }}>{id}</span>
            </div>
          ))}
        </div>

        {/* Grid */}
        <div style={{ display: 'flex' }}>
          {/* Lijevi labeli */}
          <div style={{ display: 'flex', flexDirection: 'column', width: labelW, flexShrink: 0 }}>
            {ids.map((id, i) => (
              <div key={i} style={{ height: cellSize, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', paddingRight: 10, fontFamily: 'JetBrains Mono, monospace', fontSize: Math.max(8, Math.min(11, cellSize * 0.35)), color: '#64748B', whiteSpace: 'nowrap' }}>{id}</div>
            ))}
          </div>

          {/* Ćelije */}
          <div style={{ display: 'flex', flexDirection: 'column', border: '1px solid rgba(148,163,184,0.15)', borderRadius: 6, overflow: 'hidden' }}>
            {data.map((row, i) => (
              <div key={i} style={{ display: 'flex' }}>
                {row.map((v, j) => {
                  const pct = Math.round(v * 100)
                  const isDiag = i === j
                  const isSel  = selected?.i === i && selected?.j === j
                  const bg     = isDiag ? '#1F2937' : colorFor(pct)
                  const textColor = pct > 45 && pct < 75 ? '#0A0F1C' : '#FFFFFF'

                  return (
                    <div key={j}
                      onMouseEnter={e => setTip({ x: e.clientX, y: e.clientY, a: ids[i], b: ids[j], pct, isDiag })}
                      onMouseMove={e  => setTip({ x: e.clientX, y: e.clientY, a: ids[i], b: ids[j], pct, isDiag })}
                      onMouseLeave={() => setTip(null)}
                      onClick={() => handleClick(i, j)}
                      style={{
                        width: cellSize, height: cellSize, flexShrink: 0,
                        background: bg,
                        border: isSel ? '2px solid #00D4FF' : '1px solid rgba(10,15,28,0.3)',
                        cursor: isDiag ? 'default' : 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        boxSizing: 'border-box',
                        outline: isSel ? '2px solid rgba(0,212,255,0.4)' : 'none',
                        transition: 'filter .1s',
                      }}>
                      {showPct && !isDiag && (
                        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: Math.max(8, cellSize * 0.28), fontWeight: 700, color: textColor, userSelect: 'none', lineHeight: 1 }}>{pct}%</span>
                      )}
                      {isDiag && showPct && (
                        <span style={{ fontSize: cellSize * 0.3, color: '#475569' }}>—</span>
                      )}
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legenda */}
      <div style={{ marginTop: 20, display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 11, color: '#94A3B8', letterSpacing: '0.04em', textTransform: 'uppercase' }}>Similarity</span>
        <div style={{ display: 'flex', height: 10, width: 200, borderRadius: 4, overflow: 'hidden', border: '1px solid rgba(148,163,184,0.10)' }}>
          {Array.from({ length: 40 }).map((_, i) => (
            <div key={i} style={{ flex: 1, background: colorFor(i * 2.5 + 1) }}/>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 16, fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}>
          <span style={{ color: '#64748B' }}>0%</span>
          <span style={{ color: '#00D4FF' }}>50%</span>
          <span style={{ color: '#F59E0B' }}>75%</span>
          <span style={{ color: '#EF4444' }}>100%</span>
        </div>
        {selected && (
          <span style={{ marginLeft: 16, fontSize: 11, color: '#00D4FF' }}>
            Klikni ponovo za deselect · skrolaj dolje za usporedbu
          </span>
        )}
      </div>

      {/* Tooltip */}
      {tip && !tip.isDiag && (
        <div style={{ position: 'fixed', left: tip.x + 14, top: tip.y + 14, background: 'rgba(10,15,28,0.97)', border: '1px solid rgba(0,212,255,0.4)', padding: '10px 14px', borderRadius: 8, zIndex: 200, fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#F8FAFC', boxShadow: '0 8px 24px rgba(0,0,0,0.5)', pointerEvents: 'none' }}>
          <div style={{ color: '#94A3B8', fontSize: 10, marginBottom: 4 }}>{tip.a} ↔ {tip.b}</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: colorFor(tip.pct), lineHeight: 1 }}>{tip.pct}%</div>
          <div style={{ fontSize: 10, color: '#64748B', marginTop: 3 }}>
            {tip.pct >= 80 ? 'Very high similarity' : tip.pct >= 60 ? 'High similarity' : tip.pct >= 40 ? 'Moderate' : 'Low similarity'}
          </div>
          <div style={{ fontSize: 9, color: '#475569', marginTop: 4 }}>Klikni za usporedbu koda</div>
        </div>
      )}
    </div>
  )
}
