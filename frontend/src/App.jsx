import { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import AnalyzeScreen from './screens/AnalyzeScreen'
import BatchScreen from './screens/BatchScreen'
import SimilarityScreen from './screens/SimilarityScreen'
import DetailScreen from './screens/DetailScreen'

export default function App() {
  const [screen, setScreen] = useState('analyze')
  const [detailRow, setDetailRow] = useState(null)
  const [serverOk, setServerOk] = useState(null)

  useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(d => setServerOk(d.model_loaded))
      .catch(() => setServerOk(false))
  }, [])

  const navigate = (s) => { setScreen(s); setDetailRow(null) }
  const openDetail = (row) => { setDetailRow(row); setScreen('detail') }

  return (
    <div style={{ minHeight: '100vh', background: '#0A0F1C', position: 'relative' }}>
      {/* Atmospheric glow */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
        background: 'radial-gradient(ellipse 1200px 600px at 50% -10%, rgba(0,212,255,0.08), transparent 60%)',
      }}/>

      <div style={{ position: 'relative', zIndex: 1 }}>
        <Navbar active={screen === 'detail' ? 'batch' : screen} onNavigate={navigate}/>

        {/* Server status banner */}
        {serverOk === false && (
          <div style={{
            background: 'rgba(239,68,68,0.12)', borderBottom: '1px solid rgba(239,68,68,0.25)',
            padding: '10px 80px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: '#EF4444',
          }}>
            <span>⚠</span>
            <span>Flask server not reachable. Start it with: <code style={{ fontFamily: 'JetBrains Mono, monospace', background: 'rgba(239,68,68,0.12)', padding: '2px 6px', borderRadius: 4 }}>python app.py</code></span>
          </div>
        )}

        {serverOk === true && screen === 'analyze' && (
          <div style={{
            background: 'rgba(16,185,129,0.08)', borderBottom: '1px solid rgba(16,185,129,0.15)',
            padding: '8px 80px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, color: '#10B981',
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981', display: 'inline-block' }}/>
            Server connected · Model loaded
          </div>
        )}

        {screen === 'analyze'    && <AnalyzeScreen/>}
        {screen === 'batch'      && <BatchScreen onOpenRow={openDetail}/>}
        {screen === 'similarity' && <SimilarityScreen/>}
        {screen === 'detail'     && <DetailScreen row={detailRow} onBack={() => setScreen('batch')}/>}
      </div>
    </div>
  )
}
