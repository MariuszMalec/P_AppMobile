import { useEffect, useState } from 'react'
import API_URL from './api'

const DESCRIPTIONS = {
  summary: 'Duża liczba to sesje, mniejsza to suma godzin. Tydzień liczony od poniedziałku do niedzieli. Tylko aktywni klienci.',
  days_in_month: 'Liczba sesji w każdym dniu wybranego miesiąca. Pomarańczowy słupek to dzisiaj.',
  last_weeks: 'Liczba sesji w kolejnych tygodniach.',
  last_months: 'Liczba sesji w kolejnych miesiącach.',
  weekdays: 'Liczba sesji w poszczególne dni tygodnia.',
  top_clients: 'Klienci z największą liczbą sesji (obok liczba godzin).',
}

export default function Stats() {
  const [monthOffset, setMonthOffset] = useState(0)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setError('')
    fetch(`${API_URL}/stats/api?month_offset=${monthOffset}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(setData)
      .catch((e) => setError(e.message))
  }, [monthOffset])

  return (
    <main className="clients-page stats-page">
      <h1>Statystyki</h1>

      <div className="stats-month-nav">
        <button className="week-button" onClick={() => setMonthOffset(monthOffset - 1)}>←</button>
        <button className="today-button" onClick={() => setMonthOffset(0)}>
          {data?.month_label || 'Miesiąc'}
        </button>
        <button className="week-button" onClick={() => setMonthOffset(monthOffset + 1)}>→</button>
      </div>

      {error && <p className="error">Błąd: {error}</p>}
      {!data && !error && <p>Ładowanie...</p>}

      {data?.sections.map((sec) => (
        <section key={sec.key} className="stats-section">
          <h2>{sec.title}</h2>
          {DESCRIPTIONS[sec.key] && <p className="stats-desc">{DESCRIPTIONS[sec.key]}</p>}

          {sec.type === 'cards' && (
            <div className="stats-cards stats-cards-2">
              {sec.items.map((it) => (
                <div className="stat-card" key={it.label}>
                  <b>{it.value}</b>
                  <span>{it.label}</span>
                  {it.sub && <small>{it.sub}</small>}
                </div>
              ))}
            </div>
          )}

          {sec.type !== 'cards' && sec.items.length > 12 && (
            <div className="stat-cols">
              {sec.items.map((it) => (
                <div className="stat-col" key={it.label} title={`${it.label}: ${it.value}`}>
                  <span className="stat-col-n">{it.value || ''}</span>
                  <div className="stat-col-bar">
                    <div
                      className={it.highlight ? 'hl' : ''}
                      style={{ height: `${it.pct}%` }}
                    />
                  </div>
                  <span className={it.highlight ? 'stat-col-l hl' : 'stat-col-l'}>{it.label}</span>
                </div>
              ))}
            </div>
          )}

          {sec.type !== 'cards' && sec.items.length <= 12 &&
            sec.items.map((it) => (
              <div className="stat-row" key={it.label}>
                <span className="stat-name">{it.label}</span>
                <div className="stat-bar">
                  <div style={{ width: `${it.pct}%` }} />
                </div>
                <span className="stat-n">
                  {it.value}
                  {it.sub ? <small> · {it.sub}</small> : null}
                </span>
              </div>
            ))}
        </section>
      ))}
    </main>
  )
}
