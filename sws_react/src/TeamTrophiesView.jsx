import { useEffect, useMemo, useState } from 'react'
import API_URL from './api'

const imgUrl = (p) => {
  if (!p) return ''
  return p.startsWith('http') ? p : `${API_URL}${p}`
}

export default function TeamTrophiesView({ team, teams = [], onBack }) {
  const [current, setCurrent] = useState(team)
  const [seasons, setSeasons] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [light, setLight] = useState(false)

  // unikalne drużyny po nazwie (do listy rozwijanej)
  const teamOptions = useMemo(() => {
    const map = new Map()
    teams.forEach(t => { if (!map.has(t.Name)) map.set(t.Name, t) })
    if (!map.has(team.Name)) map.set(team.Name, team)
    return [...map.values()].sort((a, b) => a.Name.localeCompare(b.Name))
  }, [teams, team])

  useEffect(() => {
    setLoading(true)
    setError('')
    fetch(`${API_URL}/api/teams/${current.Id}/trophies_by_season`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(data => {
        setSeasons([...data].sort((a, b) => a.Season - b.Season))
        setLoading(false)
      })
      .catch(e => {
        setError(e.message)
        setLoading(false)
      })
  }, [current.Id])

  // kolumny = unikalne puchary
  const columns = useMemo(() => {
    const map = new Map()
    seasons.forEach(s =>
      s.Trophies.forEach(t => {
        if (!map.has(t.Name)) {
          map.set(t.Name, { name: t.Name, picture: t.Picture })
        }
      })
    )
    return [...map.values()]
  }, [seasons])

  const cellOf = (season, name) =>
    season.Trophies.find(t => t.Name === name)

  const sums = columns.map(c => {
    let won = 0
    let lost = 0
    seasons.forEach(s => {
      const t = cellOf(s, c.name)
      if (t) t.Lose ? lost++ : won++
    })
    return { won, lost }
  })

  return (
    <div className={`tv-page ${light ? 'tv-light-theme' : ''}`}>
      <div className="tv-topbar">
        <button onClick={() => setLight(!light)}>
          {light ? '🌙 Ciemny' : '☀️ Jasny'}
        </button>
        <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          ↑ Góra
        </button>
      </div>

      <h1 className="tv-title">🏆 Trofea drużyny</h1>

      <div className="tv-controls">
        <select
          value={current.Name}
          onChange={e =>
            setCurrent(teamOptions.find(t => t.Name === e.target.value))
          }
        >
          {teamOptions.map(t => (
            <option key={t.Name} value={t.Name}>{t.Name}</option>
          ))}
        </select>
        <button className="tv-back" onClick={onBack}>← Teams</button>
      </div>

      <h2 className="tv-team">{current.Name}</h2>

      {loading && <div className="tv-msg">Ładowanie...</div>}
      {error && <div className="tv-msg">BŁĄD: {error}</div>}
      {!loading && !error && seasons.length === 0 && (
        <div className="tv-msg">Brak pucharów</div>
      )}

      {!loading && !error && seasons.length > 0 && (
        <div className="tv-scroll">
          <table className="tv-table">
            <thead>
              <tr>
                <th>Rok</th>
                {columns.map(c => (
                  <th key={c.name}>
                    {c.picture && <img src={imgUrl(c.picture)} alt="" />}
                    <div>{c.name}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {seasons.map(s => (
                <tr key={s.Season}>
                  <td className="tv-year">{s.Season}</td>
                  {columns.map(c => {
                    const t = cellOf(s, c.name)
                    return (
                      <td key={c.name}>
                        {!t ? '–' : t.Lose ? '❌' : '✅'}
                      </td>
                    )
                  })}
                </tr>
              ))}
              <tr className="tv-sum">
                <td className="tv-year">Σ</td>
                {sums.map((x, i) => (
                  <td key={i}>
                    <div>✅ {x.won}</div>
                    <div>❌ {x.lost}</div>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
