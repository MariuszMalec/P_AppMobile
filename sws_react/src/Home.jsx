import { useEffect, useMemo, useState } from 'react'

function Counter({ value }) {
  const [n, setN] = useState(0)
  useEffect(() => {
    if (!value) return
    let raf
    let start = null
    const step = ts => {
      if (start === null) start = ts
      const p = Math.min((ts - start) / 1200, 1)
      setN(Math.round(value * (1 - Math.pow(1 - p, 3))))
      if (p < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [value])
  return <>{value ? n : 0}</>
}

export default function Home({ teams, theme, onToggleTheme, onTeams, onMatrix, onTrophies, onStats, onScorers }) {
  const stats = useMemo(() => ({
    teams: new Set(teams.map(t => t.Name)).size,
    seasons: new Set(teams.map(t => t.Season)).size,
    trophies: teams.filter(t => t.TrophyModelId).length,
  }), [teams])

  const tiles = [
    { cls: 'g1', ico: '🛡️', title: 'Drużyny', desc: 'Lista, filtry, edycja', on: onTeams },
    { cls: 'g2', ico: '🏆', title: 'Trofea', desc: 'Galeria pucharów', on: onTrophies },
    { cls: 'g3', ico: '📊', title: 'Lata × trofea', desc: 'Wygrane i przegrane', on: onMatrix },
    { cls: 'g4', ico: '⚽', title: 'Top Scorer', desc: 'Szukaj po strzelcu', on: onScorers },
    { cls: 'g1', ico: '📊', title: 'Statystyki', desc: 'Rankingi i skuteczność', on: onStats },
  ]

  return (
    <div className="home-page">
      <div className="home-blob hb1" />
      <div className="home-blob hb2" />
      <div className="home-blob hb3" />

      <div className="home-wrap">
        <div className="home-hero">
          <div className="home-top">
            <span className="home-pill">🏆 Sports Manager</span>
            <button className="home-pill home-theme" onClick={onToggleTheme}>
              {theme === 'dark' ? '☀️ Jasny' : '🌙 Ciemny'}
            </button>
          </div>
          <h1>
            Twoje drużyny.<br />
            <span className="home-grad">Twoje trofea.</span>
          </h1>
          <p>Sezony, wygrane i porażki w jednym miejscu.</p>
        </div>

        <div className="home-stats">
          <div className="home-stat"><div className="home-num"><Counter value={stats.teams} /></div><div className="home-lbl">Drużyny</div></div>
          <div className="home-stat"><div className="home-num"><Counter value={stats.seasons} /></div><div className="home-lbl">Sezony</div></div>
          <div className="home-stat"><div className="home-num"><Counter value={stats.trophies} /></div><div className="home-lbl">Trofea</div></div>
        </div>

        <div className="home-grid">
          {tiles.map(t => (
            <button
              key={t.title}
              className={`home-tile ${t.soon ? 'home-soon' : ''}`}
              onClick={t.soon ? undefined : t.on}
            >
              <div className={`home-ico ${t.cls}`}>{t.ico}</div>
              <div className="home-text">
                <h3>{t.title}</h3>
                <p>{t.soon ? 'wkrótce' : t.desc}</p>
              </div>
              <span className="home-arrow">›</span>
            </button>
          ))}
        </div>

        <div className="home-foot">SWS · Sports Manager</div>
      </div>
    </div>
  )
}
