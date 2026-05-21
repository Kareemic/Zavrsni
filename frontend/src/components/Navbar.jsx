import { useState } from 'react'
import { Button } from './primitives'

function NavLink({ active, onClick, children }) {
  const [hover, setHover] = useState(false)
  return (
    <button onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        background: active ? 'rgba(0,212,255,0.08)' : 'transparent',
        border: 'none', padding: '8px 14px', borderRadius: 8,
        fontFamily: 'Inter, sans-serif', fontSize: 14,
        fontWeight: active ? 600 : 500,
        color: active ? '#00D4FF' : hover ? '#F8FAFC' : '#CBD5E1',
        cursor: 'pointer', transition: 'all .12s cubic-bezier(0.22,1,0.36,1)',
      }}>
      {children}
    </button>
  )
}

export default function Navbar({ active, onNavigate }) {
  const tabs = [
    { id: 'analyze',    label: 'Analyze' },
    { id: 'batch',      label: 'Batch Upload' },
    { id: 'similarity', label: 'Similarity' },
  ]
  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 50, height: 72,
      background: 'rgba(10,15,28,0.80)',
      backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)',
      borderBottom: '1px solid rgba(148,163,184,0.12)',
    }}>
      <div style={{
        maxWidth: 1280, height: '100%', margin: '0 auto',
        padding: '0 80px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}
          onClick={() => onNavigate('analyze')}>
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
            <path d="M16 1L2 6v10c0 8.5 5.8 16 14 18 8.2-2 14-9.5 14-18V6L16 1z" fill="#111827" stroke="#00D4FF" strokeWidth="1.5"/>
            <path d="M10 16l4 4 8-8" stroke="#00D4FF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em', color: '#F8FAFC' }}>
            Code<span style={{ color: '#00D4FF' }}>Sentinel</span>
          </div>
        </div>
        <nav style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          {tabs.map(t => (
            <NavLink key={t.id} active={active === t.id} onClick={() => onNavigate(t.id)}>
              {t.label}
            </NavLink>
          ))}
        </nav>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%',
            background: 'linear-gradient(135deg, #00D4FF, #06B6D4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#0A0F1C', fontWeight: 700, fontSize: 12,
          }}>CS</div>
        </div>
      </div>
    </header>
  )
}
