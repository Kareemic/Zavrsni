import { Card, Label, Badge, Icon } from './primitives'

function SuspiciousPair({ a, b, similarity }) {
  const color = similarity >= 85 ? '#EF4444' : '#F59E0B'
  return (
    <Card hoverable style={{ padding: '16px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 600, color: '#F8FAFC' }}>{a}</span>
            <Icon name="chevronRight" size={14} color="#64748B"/>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 600, color: '#F8FAFC' }}>{b}</span>
          </div>
          <div style={{ fontSize: 12, color: '#64748B' }}>High structural similarity detected</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 700, color, lineHeight: 1 }}>
            {similarity}<span style={{ fontSize: 14 }}>%</span>
          </div>
          <div style={{ fontSize: 10, color: '#64748B', letterSpacing: '0.04em', textTransform: 'uppercase', marginTop: 4 }}>Similar</div>
        </div>
      </div>
    </Card>
  )
}

export { SuspiciousPair }

export default function DetailSidebar({ features }) {
  const groups = features.reduce((acc, f) => {
    const cat = f.category || 'Other';
    (acc[cat] = acc[cat] || []).push(f)
    return acc
  }, {})

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {Object.entries(groups).map(([cat, items]) => (
        <Card key={cat} style={{ padding: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <Label style={{ marginBottom: 0 }}>{cat}</Label>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#64748B' }}>{items.length}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {items.map((f, i) => {
              const color = f.severity === 'high' ? '#EF4444' : f.severity === 'medium' ? '#F59E0B' : '#10B981'
              const pct = f.severity === 'high' ? 85 : f.severity === 'medium' ? 55 : 22
              return (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
                    <span style={{ fontSize: 12, color: '#CBD5E1' }}>{f.name}</span>
                    <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color }}>{f.value}</span>
                  </div>
                  <div style={{ height: 3, background: 'rgba(148,163,184,0.10)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: color }}/>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      ))}
    </div>
  )
}
