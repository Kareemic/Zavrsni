import { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import AnalyzeScreen from './screens/AnalyzeScreen'
import BatchScreen from './screens/BatchScreen'
import SimilarityScreen from './screens/SimilarityScreen'
import DetailScreen from './screens/DetailScreen'

// Hash-based routing — svaki ekran ima vlastiti URL fragment
// Tako browser back/forward gumb rade ispravno
const SCREEN_TO_HASH = {
  analyze:    '#analyze',
  batch:      '#batch',
  similarity: '#similarity',
  detail:     '#detail',
}
const HASH_TO_SCREEN = Object.fromEntries(
  Object.entries(SCREEN_TO_HASH).map(([k, v]) => [v, k])
)

function getScreenFromHash() {
  return HASH_TO_SCREEN[window.location.hash] || 'analyze'
}

export default function App() {
  const [screen, setScreen]     = useState(getScreenFromHash)
  const [detailRow, setDetailRow] = useState(null)
  const [serverOk, setServerOk]  = useState(null)

  // Health check
  useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(d => setServerOk(d.model_loaded))
      .catch(() => setServerOk(false))
  }, [])

  // Slušamo browser back/forward
  useEffect(() => {
    const onPop = () => {
      const s = getScreenFromHash()
      setScreen(s)
      // Ako se vraćamo s detail-a, detailRow ostaje — batch zadržava state
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  // Navigacija — pushState mijenja URL i bilježi u history
  const navigate = (s) => {
    if (s !== 'batch' && s !== 'detail') setDetailRow(null)
    window.history.pushState({ screen: s }, '', SCREEN_TO_HASH[s])
    setScreen(s)
  }

  const openDetail = (row) => {
    setDetailRow(row)
    window.history.pushState({ screen: 'detail' }, '', '#detail')
    setScreen('detail')
  }

  const backToBatch = () => {
    window.history.pushState({ screen: 'batch' }, '', '#batch')
    setScreen('batch')
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0A0F1C', position: 'relative' }}>
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
        background: 'radial-gradient(ellipse 1200px 600px at 50% -10%, rgba(0,212,255,0.08), transparent 60%)',
      }}/>

      <div style={{ position: 'relative', zIndex: 1 }}>
        <Navbar active={screen === 'detail' ? 'batch' : screen} onNavigate={navigate}/>

        {serverOk === false && (
          <div style={{
            background: 'rgba(239,68,68,0.12)', borderBottom: '1px solid rgba(239,68,68,0.25)',
            padding: '10px 80px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: '#EF4444',
          }}>
            <span>⚠</span>
            <span>Flask server not reachable — <code style={{ fontFamily: 'JetBrains Mono, monospace', background: 'rgba(239,68,68,0.12)', padding: '2px 6px', borderRadius: 4 }}>python app.py</code></span>
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
        {screen === 'similarity' && <SimilarityScreen/>}

        {/* BatchScreen ostaje montiran dok smo u batch/detail ciklusu */}
        <div style={{ display: screen === 'batch' || screen === 'detail' ? 'block' : 'none' }}>
          <div style={{ display: screen === 'batch' ? 'block' : 'none' }}>
            <BatchScreen onOpenRow={openDetail}/>
          </div>
          <div style={{ display: screen === 'detail' ? 'block' : 'none' }}>
            <DetailScreen row={detailRow} onBack={backToBatch}/>
          </div>
        </div>
      </div>
    </div>
  )
}
