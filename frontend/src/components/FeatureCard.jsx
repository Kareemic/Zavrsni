import { Card, Badge, Icon, Label } from './primitives'

export function FeatureCard({ name, value, severity = 'low', unit = '', icon }) {
  const tones = {
    high:   { color: '#EF4444', label: 'HIGH',   tone: 'red',   pct: 85 },
    medium: { color: '#F59E0B', label: 'MEDIUM', tone: 'amber', pct: 55 },
    low:    { color: '#10B981', label: 'LOW',    tone: 'green', pct: 22 },
  }
  const t = tones[severity] || tones.low
  return (
    <Card hoverable>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#94A3B8' }}>
          {icon && <Icon name={icon} size={14}/>}
          <Label style={{ marginBottom: 0 }}>{name}</Label>
        </div>
        <Badge tone={t.tone} size="sm">{t.label}</Badge>
      </div>
      <div style={{
        fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 700,
        color: '#F8FAFC', lineHeight: 1, fontVariantNumeric: 'tabular-nums',
      }}>{value}<span style={{ fontSize: 14, color: '#64748B', marginLeft: 4 }}>{unit}</span></div>
      <div style={{ height: 4, background: 'rgba(148,163,184,0.10)', borderRadius: 2, marginTop: 14, overflow: 'hidden' }}>
        <div style={{ width: `${t.pct}%`, height: '100%', background: t.color, borderRadius: 2, transition: 'width .6s cubic-bezier(0.22,1,0.36,1)' }}/>
      </div>
    </Card>
  )
}

export function StatCard({ label, value, delta, deltaColor = '#94A3B8', icon, iconColor = '#00D4FF' }) {
  return (
    <Card>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
        <Label style={{ marginBottom: 0 }}>{label}</Label>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: `${iconColor}15`, border: `1px solid ${iconColor}30`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon name={icon} size={16} color={iconColor}/>
        </div>
      </div>
      <div style={{
        fontFamily: 'JetBrains Mono, monospace', fontSize: 32, fontWeight: 700,
        color: '#F8FAFC', lineHeight: 1, fontVariantNumeric: 'tabular-nums',
      }}>{value}</div>
      {delta && <div style={{ fontSize: 12, color: deltaColor, marginTop: 8 }}>{delta}</div>}
    </Card>
  )
}
