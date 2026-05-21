import { useState } from 'react'
import { Icon } from './primitives'

export default function Dropzone({ files = [], onUpload }) {
  const [dragOver, setDragOver] = useState(false)
  return (
    <div
      onDragOver={e => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={e => { e.preventDefault(); setDragOver(false); onUpload && onUpload(e.dataTransfer.files) }}
      onClick={() => { const i = document.createElement('input'); i.type = 'file'; i.multiple = true; i.accept = '.py,.js,.java,.cpp,.ts,.go,.rs,.rb,.c,.h'; i.onchange = e => onUpload && onUpload(e.target.files); i.click() }}
      style={{
        border: `1.5px dashed ${dragOver ? 'rgba(0,212,255,0.6)' : 'rgba(148,163,184,0.25)'}`,
        borderRadius: 12, padding: '48px 24px', textAlign: 'center',
        background: dragOver ? 'rgba(0,212,255,0.04)' : 'rgba(17,24,39,0.5)',
        cursor: 'pointer', transition: 'all .12s cubic-bezier(0.22,1,0.36,1)',
        backdropFilter: 'blur(20px)',
      }}>
      <div style={{
        width: 56, height: 56, margin: '0 auto 18px', borderRadius: 12,
        background: 'rgba(0,212,255,0.10)', border: '1px solid rgba(0,212,255,0.25)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon name="upload" size={24} color="#00D4FF"/>
      </div>
      <div style={{ fontSize: 18, fontWeight: 600, color: '#F8FAFC', marginBottom: 6 }}>
        {files.length > 0 ? `${files.length} files ready to analyze` : 'Drop student files here or click to upload'}
      </div>
      <div style={{ fontSize: 13, color: '#64748B' }}>
        Accepts <span style={{ fontFamily: 'JetBrains Mono, monospace', color: '#94A3B8' }}>.py .js .java .cpp .ts .go .rs</span> · max 200 files
      </div>
      {files.length > 0 && (
        <div style={{ marginTop: 20, display: 'flex', justifyContent: 'center', gap: 6, flexWrap: 'wrap', maxWidth: 600, marginLeft: 'auto', marginRight: 'auto' }}>
          {files.slice(0, 10).map((f, i) => (
            <span key={i} style={{
              fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
              padding: '4px 10px', background: 'rgba(0,212,255,0.08)',
              border: '1px solid rgba(0,212,255,0.20)', borderRadius: 6, color: '#00D4FF',
            }}>{f.name || f}</span>
          ))}
          {files.length > 10 && <span style={{ fontSize: 11, color: '#64748B', alignSelf: 'center' }}>+{files.length - 10} more</span>}
        </div>
      )}
    </div>
  )
}
