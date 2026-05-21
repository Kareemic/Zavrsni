import { useState, useEffect } from 'react'
import { Badge } from './primitives'

export default function ResultGauge({ value, size = 200, animate = true }) {
  const [display, setDisplay] = useState(animate ? 0 : value)

  useEffect(() => {
    if (!animate) { setDisplay(value); return }
    let raf, start
    const dur = 800
    const tick = (t) => {
      if (!start) start = t
      const p = Math.min((t - start) / dur, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      setDisplay(Math.round(value * eased))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value, animate])

  const color = value >= 70 ? '#EF4444' : value >= 40 ? '#F59E0B' : '#10B981'
  const verdict = value >= 70 ? 'LIKELY AI-GENERATED' : value >= 40 ? 'POSSIBLY AI-GENERATED' : 'LIKELY HUMAN-WRITTEN'
  const tone = value >= 70 ? 'red' : value >= 40 ? 'amber' : 'green'
  const r = 42, c = 2 * Math.PI * r
  const offset = c - (display / 100) * c

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
          <circle cx="50" cy="50" r={r} fill="none" stroke="#1F2937" strokeWidth="8"/>
          <circle cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset .1s linear', filter: `drop-shadow(0 0 6px ${color}66)` }}/>
        </svg>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: size * 0.26, fontWeight: 700,
            color: '#F8FAFC', lineHeight: 1, fontVariantNumeric: 'tabular-nums',
          }}>{display}<span style={{ color, fontSize: size * 0.13 }}>%</span></div>
          <div style={{ fontSize: 10, color: '#64748B', letterSpacing: '0.08em', marginTop: 4, textTransform: 'uppercase' }}>AI probability</div>
        </div>
      </div>
      <Badge tone={tone}>{verdict}</Badge>
      <div style={{ width: '100%', maxWidth: 240 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#64748B', marginBottom: 6, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
          <span>Confidence</span>
          <span style={{ color: '#CBD5E1', fontFamily: 'JetBrains Mono, monospace' }}>—</span>
        </div>
        <div style={{ height: 4, background: 'rgba(148,163,184,0.10)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ width: '100%', height: '100%', background: `linear-gradient(90deg, ${color}, ${color}aa)`, borderRadius: 2 }}/>
        </div>
      </div>
    </div>
  )
}
