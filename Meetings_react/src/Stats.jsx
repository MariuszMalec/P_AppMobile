import { useEffect, useState } from 'react'
import API_URL from './api'

function collectSessions(node, out = new Map()) {
  if (Array.isArray(node)) node.forEach((n) => collectSessions(n, out))
  else if (node && typeof node === 'object') {
    if (node.session_id !== undefined) out.set(node.session_id, node)
    else Object.values(node).forEach((n) => collectSessions(n, out))
  }
  return out
}

export default function Stats() {
  const [state, setState] = useState({ loading: true })

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/clients/list?active=1`).then((r) => r.json()),
      fetch(`${API_URL}/clients/list?active=0`).then((r) => r.json()),
      fetch(`${API_URL}/sessions/api?week_offset=0`).then((r) => r.json()),
    ])
      .then(([active, inactive, week]) => {
        const sessions = [...collectSessions(week).values()]
        const byClient = {}
        sessions.forEach((s) => {
          byClient[s.client_id] = (byClient[s.client_id] || 0) + 1
        })
        const names = {}
        ;[...active, ...inactive].forEach((c) => {
          names[c.Id] = `${c.FirstName || ''} ${c.LastName || ''}`.trim()
        })
        const ranking = Object.entries(byClient)
          .map(([id, n]) => ({ id, n, name: names[id] || `Klient ${id}` }))
          .sort((a, b) => b.n - a.n)
        setState({
          loading: false,
          active: active.length,
          inactive: inactive.length,
          weekCount: sessions.length,
          ranking,
        })
      })
      .catch((e) => setState({ loading: false, error: e.message }))
  }, [])

  if (state.loading) return <main className="clients-page"><h1>Statystyki</h1><p>Ładowanie...</p></main>
  if (state.error) return <main className="clients-page"><h1>Statystyki</h1><p className="error">Błąd: {state.error}</p></main>

  const max = Math.max(1, ...state.ranking.map((r) => r.n))
  return (
    <main className="clients-page stats-page">
      <h1>Statystyki</h1>
      <div className="stats-cards">
        <div className="stat-card"><b>{state.active}</b><span>Aktywni klienci</span></div>
        <div className="stat-card"><b>{state.inactive}</b><span>Nieaktywni</span></div>
        <div className="stat-card"><b>{state.weekCount}</b><span>Sesje w tym tygodniu</span></div>
      </div>
      <h2>Sesje w tym tygodniu wg klienta</h2>
      {state.ranking.length === 0 && <p>Brak sesji w tym tygodniu.</p>}
      {state.ranking.map((r) => (
        <div className="stat-row" key={r.id}>
          <span className="stat-name">{r.name}</span>
          <div className="stat-bar"><div style={{ width: `${(r.n / max) * 100}%` }} /></div>
          <span className="stat-n">{r.n}</span>
        </div>
      ))}
    </main>
  )
}
