import { useEffect, useState } from 'react'
import API_URL from './api'

const BLOCKS = [
  ['by_team', '🏆 Puchary wg drużyny', 'c1', false],
  ['by_trophy', '🥇 Najczęściej wygrywane', 'c2', false],
  ['lost_trophy', '💔 Najczęściej przegrywane', 'c4', false],
  ['scorers', '⚽ Królowie strzelców', 'c3', false],
  ['countries', '🌍 Kraje', 'c4', false],
  ['seasons', '📅 Najlepsze sezony', 'c1', true],
]

function Bars({ items, color }) {
  if (!items || items.length === 0) return <div className="s-empty">Brak danych</div>
  return items.map(i => (
    <div className="s-bar-row" key={i.label}>
      <span className="s-bar-lbl" title={i.label}>{i.label}</span>
      <div className="s-bar"><div className={`s-fill ${color}`} style={{ width: `${i.pct}%` }} /></div>
      <span className="s-bar-val">{i.value}</span>
    </div>
  ))
}

export default function Stats({ theme, onToggleTheme, onBack }) {
  const [d, setD] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API_URL}/api/stats`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setD)
      .catch(e => setError(e.message))
  }, [])

  return (
    <div className="stats-page">
      <div className="s-wrap">
        <div className="s-top">
          <button className="s-pill" onClick={onBack}>← Home</button>
          <button className="s-pill" onClick={onToggleTheme}>
            {theme === 'dark' ? '☀️ Jasny' : '🌙 Ciemny'}
          </button>
        </div>

        <h1>📊 Statystyki</h1>

        {error && <div className="s-empty">BŁĄD: {error}</div>}
        {!d && !error && <div className="s-empty">Ładowanie...</div>}

        {d && (
          <div className="s-insights">
            <div className="s-card s-wide">
              <h4>Bilans trofeów</h4>
              <div className="s-record">
                <div className="s-win" style={{ flex: d.wins || 1 }}>✅ {d.wins}</div>
                <div className="s-lose" style={{ flex: d.losses || 1 }}>❌ {d.losses}</div>
              </div>
              <div className="s-rate">Skuteczność: <b>{d.rate}%</b></div>
            </div>

            {BLOCKS.map(([key, title, color, wide]) => (
              <div className={`s-card ${wide ? 's-wide' : ''}`} key={key}>
                <h4>{title}</h4>
                <Bars items={d[key]} color={color} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
