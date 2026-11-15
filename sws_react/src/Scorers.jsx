import { useEffect, useState } from 'react'
import API_URL from './api'

export default function Scorers({ theme, onToggleTheme, onBack }) {
  const [names, setNames] = useState([])
  const [name, setName] = useState('')
  const [rows, setRows] = useState([])
  const [career, setCareer] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    const q = name ? `?name=${encodeURIComponent(name)}` : ''
    fetch(`${API_URL}/api/scorers${q}`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(d => {
        setNames(d.names)
        setRows(d.rows)
        setCareer(d.career)
        setError('')
      })
      .catch(e => setError(e.message))
  }, [name])

  return (
    <div className="tr-page">
      <div className="tr-top">
        <button className="tr-back" onClick={onBack}>← Home</button>
        <button className="tr-back" onClick={onToggleTheme}>
          {theme === 'dark' ? '☀️ Jasny' : '🌙 Ciemny'}
        </button>
      </div>
      <h1 style={{ fontSize: 22, margin: '0 0 10px' }}>⚽ Strzelcy drużyny</h1>

      <select className="tr-search" value={name} onChange={e => setName(e.target.value)}>
        <option value="">— wybierz drużynę —</option>
        {names.map(n => <option key={n} value={n}>{n}</option>)}
      </select>

      {error && <div className="tr-msg">BŁĄD: {error}</div>}

      {name && rows.length === 0 && !error && (
        <div className="tr-msg">Brak strzelców dla tej drużyny.</div>
      )}

      {rows.length > 0 && (
        <>
          <h2 className="sc-h">{name}</h2>
          <table className="sc-table">
            <thead>
              <tr><th>Rok</th><th>Zawodnik</th><th>LGE</th><th>CUP</th><th>EUR</th><th>TOT</th></tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className={r.Top ? 'sc-top' : ''}>
                  <td>{r.Season}</td>
                  <td>{r.Top ? '🥇 ' : ''}{r.Player}</td>
                  <td>{r.League}</td><td>{r.Cup}</td><td>{r.Europe}</td><td>{r.Total}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h2 className="sc-h">Najlepsi w historii klubu</h2>
          <table className="sc-table">
            <thead>
              <tr><th>#</th><th>Zawodnik</th><th>LGE</th><th>CUP</th><th>EUR</th><th>TOT</th></tr>
            </thead>
            <tbody>
              {career.map((c, i) => (
                <tr key={c.Player}>
                  <td>{i + 1}</td><td>{c.Player}</td>
                  <td>{c.L}</td><td>{c.C}</td><td>{c.E}</td><td><b>{c.T}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
