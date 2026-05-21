// ExplanationPanel.jsx — prikaz objašnjenja zašto je kod klasificiran ovako

import { Card, Label, Icon } from './primitives'

const SEVERITY_CONFIG = {
  high: {
    color: '#EF4444',
    bg: 'rgba(239,68,68,0.08)',
    border: 'rgba(239,68,68,0.25)',
    icon: 'xCircle',
    label: 'Strong signal',
  },
  medium: {
    color: '#F59E0B',
    bg: 'rgba(245,158,11,0.08)',
    border: 'rgba(245,158,11,0.25)',
    icon: 'alert',
    label: 'Moderate signal',
  },
  low: {
    color: '#94A3B8',
    bg: 'rgba(148,163,184,0.06)',
    border: 'rgba(148,163,184,0.15)',
    icon: 'filter',
    label: 'Weak signal',
  },
  positive: {
    color: '#10B981',
    bg: 'rgba(16,185,129,0.08)',
    border: 'rgba(16,185,129,0.25)',
    icon: 'check',
    label: 'Human indicator',
  },
}

export default function ExplanationPanel({ explanations, verdict, aiProbability }) {
  if (!explanations || explanations.length === 0) return null

  const highCount   = explanations.filter(e => e.severity === 'high').length
  const medCount    = explanations.filter(e => e.severity === 'medium').length
  const posCount    = explanations.filter(e => e.severity === 'positive').length

  return (
    <Card style={{ padding: 24, marginTop: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <Label style={{ marginBottom: 6 }}>Analysis reasoning</Label>
          <p style={{ margin: 0, fontSize: 13, color: '#64748B', lineHeight: 1.5, maxWidth: 560 }}>
            The following signals contributed to the classification. Strong signals carry the most weight;
            human indicators suggest characteristics inconsistent with AI generation.
          </p>
        </div>
        {/* Signal summary pills */}
        <div style={{ display: 'flex', gap: 8, flexShrink: 0, marginLeft: 24 }}>
          {highCount > 0 && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 999, fontSize: 11, fontWeight: 600, background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.30)', color: '#EF4444' }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#EF4444' }}/>
              {highCount} strong
            </span>
          )}
          {medCount > 0 && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 999, fontSize: 11, fontWeight: 600, background: 'rgba(245,158,11,0.12)', border: '1px solid rgba(245,158,11,0.30)', color: '#F59E0B' }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#F59E0B' }}/>
              {medCount} moderate
            </span>
          )}
          {posCount > 0 && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 999, fontSize: 11, fontWeight: 600, background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.30)', color: '#10B981' }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#10B981' }}/>
              {posCount} human
            </span>
          )}
        </div>
      </div>

      {/* Explanation items */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {explanations.map((exp, i) => {
          const cfg = SEVERITY_CONFIG[exp.severity] || SEVERITY_CONFIG.low
          return (
            <div key={i} style={{
              display: 'flex', gap: 14, alignItems: 'flex-start',
              padding: '14px 16px',
              background: cfg.bg,
              border: `1px solid ${cfg.border}`,
              borderRadius: 10,
              animation: `fadeIn .25s ease ${i * 0.04}s both`,
            }}>
              {/* Icon */}
              <div style={{
                flexShrink: 0, width: 28, height: 28, borderRadius: 8,
                background: `${cfg.color}18`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 1,
              }}>
                <Icon name={cfg.icon} size={14} color={cfg.color}/>
              </div>

              {/* Text */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
                  <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: cfg.color }}>
                    {cfg.label}
                  </span>
                  <span style={{ fontSize: 10, color: '#475569', fontFamily: 'JetBrains Mono, monospace' }}>
                    {exp.feature.replace(/_/g, ' ')}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: 13, color: '#CBD5E1', lineHeight: 1.65 }}>
                  {exp.text}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer disclaimer */}
      <div style={{
        marginTop: 16, paddingTop: 16,
        borderTop: '1px solid rgba(148,163,184,0.10)',
        fontSize: 12, color: '#475569', lineHeight: 1.55, fontStyle: 'italic',
      }}>
        CodeSentinel reports statistical signals, not academic-integrity verdicts.
        A high AI probability score should be treated as a starting point for review,
        not as conclusive evidence. Confirm findings with the student before taking any action.
      </div>
    </Card>
  )
}
