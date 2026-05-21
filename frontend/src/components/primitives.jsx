import { useState } from 'react'

export function Icon({ name, size = 18, color, strokeWidth = 1.5, style }) {
  const paths = {
    shield: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></>,
    code: <><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></>,
    upload: <><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m8 17 4-5 4 5"/></>,
    play: <polygon points="5 3 19 12 5 21 5 3"/>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>,
    search: <><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></>,
    alert: <><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><circle cx="12" cy="17" r=".5"/></>,
    check: <><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></>,
    filter: <><line x1="4" y1="6" x2="20" y2="6"/><line x1="6" y1="12" x2="18" y2="12"/><line x1="9" y1="18" x2="15" y2="18"/></>,
    chevron: <polyline points="6 9 12 15 18 9"/>,
    chevronRight: <polyline points="9 18 15 12 9 6"/>,
    chevronLeft: <polyline points="15 18 9 12 15 6"/>,
    file: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></>,
    fileCode: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="m10 13-2 2 2 2"/><path d="m14 17 2-2-2-2"/></>,
    users: <><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></>,
    chart: <><path d="M3 3v18h18"/><rect x="7" y="13" width="3" height="6"/><rect x="12" y="9" width="3" height="10"/><rect x="17" y="5" width="3" height="14"/></>,
    xCircle: <><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></>,
    external: <><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></>,
    eye: <><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></>,
    sort: <><path d="m21 16-4 4-4-4"/><path d="M17 20V4"/><path d="m3 8 4-4 4 4"/><path d="M7 4v16"/></>,
    arrowLeft: <><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></>,
    sparkles: <><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/></>,
    x: <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>,
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke={color || 'currentColor'} strokeWidth={strokeWidth}
      strokeLinecap="round" strokeLinejoin="round" style={style}>
      {paths[name] || null}
    </svg>
  )
}

export function Button({ variant = 'primary', size = 'md', icon, iconRight, children, onClick, style, disabled }) {
  const [hover, setHover] = useState(false)
  const [pressed, setPressed] = useState(false)
  const base = {
    display: 'inline-flex', alignItems: 'center', gap: 8,
    height: size === 'sm' ? 32 : size === 'lg' ? 48 : 40,
    padding: size === 'sm' ? '0 12px' : size === 'lg' ? '0 24px' : '0 18px',
    borderRadius: 8, fontFamily: 'Inter, sans-serif',
    fontSize: size === 'sm' ? 13 : size === 'lg' ? 15 : 14,
    fontWeight: 600, cursor: disabled ? 'not-allowed' : 'pointer',
    border: '1px solid transparent',
    transition: 'all .12s cubic-bezier(0.22,1,0.36,1)',
    opacity: disabled ? 0.4 : 1,
    transform: pressed ? 'scale(0.98)' : 'scale(1)',
    whiteSpace: 'nowrap',
  }
  const variants = {
    primary: {
      background: hover ? '#22E0FF' : '#00D4FF', color: '#0A0F1C',
      boxShadow: pressed ? 'none' : hover ? '0 0 32px rgba(0,212,255,0.4)' : '0 0 20px rgba(0,212,255,0.2)',
    },
    secondary: {
      background: 'transparent', color: hover ? '#F8FAFC' : '#CBD5E1',
      borderColor: hover ? 'rgba(148,163,184,0.30)' : 'rgba(148,163,184,0.12)',
    },
    ghost: {
      background: hover ? 'rgba(148,163,184,0.06)' : 'transparent',
      color: hover ? '#F8FAFC' : '#94A3B8', border: 'none',
    },
    danger: {
      background: hover ? 'rgba(239,68,68,0.20)' : 'rgba(239,68,68,0.12)',
      color: '#EF4444', borderColor: 'rgba(239,68,68,0.35)',
    },
  }
  return (
    <button style={{ ...base, ...variants[variant], ...style }}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => { setHover(false); setPressed(false) }}
      onMouseDown={() => setPressed(true)} onMouseUp={() => setPressed(false)}
      onClick={disabled ? undefined : onClick} disabled={disabled}>
      {icon && <Icon name={icon} size={16}/>}
      {children}
      {iconRight && <Icon name={iconRight} size={16}/>}
    </button>
  )
}

export function Badge({ tone = 'cyan', children, dot = true, size = 'md' }) {
  const tones = {
    cyan:  { bg: 'rgba(0,212,255,0.12)',  bd: 'rgba(0,212,255,0.30)',  fg: '#00D4FF' },
    red:   { bg: 'rgba(239,68,68,0.14)',  bd: 'rgba(239,68,68,0.35)',  fg: '#EF4444' },
    amber: { bg: 'rgba(245,158,11,0.14)', bd: 'rgba(245,158,11,0.35)', fg: '#F59E0B' },
    green: { bg: 'rgba(16,185,129,0.14)', bd: 'rgba(16,185,129,0.35)', fg: '#10B981' },
    slate: { bg: 'rgba(148,163,184,0.10)',bd: 'rgba(148,163,184,0.25)',fg: '#94A3B8' },
  }
  const t = tones[tone]
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: size === 'sm' ? '3px 8px' : '5px 11px',
      borderRadius: 999, fontSize: size === 'sm' ? 10 : 11, fontWeight: 600,
      letterSpacing: '0.04em', border: `1px solid ${t.bd}`,
      background: t.bg, color: t.fg, lineHeight: 1, whiteSpace: 'nowrap',
    }}>
      {dot && <span style={{ width: 5, height: 5, borderRadius: '50%', background: t.fg }}/>}
      {children}
    </span>
  )
}

export function LangBadge({ lang }) {
  const colors = { Python: '#3776AB', JavaScript: '#F7DF1E', Java: '#F89820', 'C++': '#00599C', Go: '#00ADD8', Rust: '#CE422B', Ruby: '#CC342D', TypeScript: '#3178C6' }
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '4px 10px', borderRadius: 6,
      fontFamily: 'JetBrains Mono, monospace', fontSize: 11, fontWeight: 500,
      background: '#1F2937', border: '1px solid rgba(148,163,184,0.12)',
      color: '#CBD5E1', lineHeight: 1,
    }}>
      <span style={{ width: 8, height: 8, borderRadius: 2, background: colors[lang] || '#94A3B8' }}/>
      {lang || 'Unknown'}
    </span>
  )
}

export function Card({ children, style, glow, hoverable, onClick }) {
  const [hover, setHover] = useState(false)
  return (
    <div onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        background: 'rgba(17,24,39,0.6)',
        border: `1px solid ${hover && hoverable ? 'rgba(148,163,184,0.24)' : 'rgba(148,163,184,0.12)'}`,
        borderRadius: 12, padding: 20,
        backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
        boxShadow: glow
          ? 'inset 0 1px 0 rgba(255,255,255,0.03), 0 0 24px rgba(0,212,255,0.15)'
          : 'inset 0 1px 0 rgba(255,255,255,0.03)',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'border-color .12s cubic-bezier(0.22,1,0.36,1)',
        ...style,
      }}>
      {children}
    </div>
  )
}

export function Input({ icon, placeholder, value, onChange, style, type = 'text' }) {
  const [focus, setFocus] = useState(false)
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      height: 40, padding: '0 14px',
      background: '#1F2937',
      border: `1px solid ${focus ? 'rgba(0,212,255,0.40)' : 'rgba(148,163,184,0.12)'}`,
      borderRadius: 8,
      boxShadow: focus ? '0 0 0 3px rgba(0,212,255,0.10)' : 'none',
      transition: 'all .12s cubic-bezier(0.22,1,0.36,1)',
      ...style,
    }}>
      {icon && <Icon name={icon} size={16} color="#94A3B8"/>}
      <input type={type} value={value} placeholder={placeholder}
        onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
        onChange={e => onChange && onChange(e.target.value)}
        style={{
          flex: 1, background: 'transparent', border: 'none', outline: 'none',
          color: '#F8FAFC', fontFamily: 'Inter, sans-serif', fontSize: 14,
        }}/>
    </div>
  )
}

export function Label({ children, style }) {
  return (
    <div style={{
      fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em',
      fontWeight: 500, color: '#94A3B8', ...style,
    }}>{children}</div>
  )
}

export function Spinner({ size = 32 }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      border: '2px solid rgba(0,212,255,0.20)',
      borderTopColor: '#00D4FF',
      animation: 'spin 0.8s linear infinite',
    }}/>
  )
}
