import { useEffect, useState } from 'react'

function Sessions({ onBack }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [weekOffset, setWeekOffset] = useState(0)
  const [selectedSession, setSelectedSession] = useState(null)
  const [editMode, setEditMode] = useState(false)
  const [editStart, setEditStart] = useState('')
  const [editEnd, setEditEnd] = useState('')
  const [editDescription, setEditDescription] = useState('')

  useEffect(() => {
    setError('')
    setData(null)

    fetch(
      `http://127.0.0.1:8001/sessions/api?week_offset=${weekOffset}`
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then((data) => {
        setData(data)
      })
      .catch((error) => {
        setError(error.message)
      })
  }, [weekOffset])

  const days = [1, 2, 3, 4, 5, 6, 7]

  const rows = data
    ? Object.entries(data.table).sort(([timeA], [timeB]) =>
        timeA.localeCompare(timeB)
      )
    : []

  function saveSession() {
    setError('')

    const formData = new FormData()

    formData.append('start', editStart)
    formData.append('end', editEnd)
    formData.append('description', editDescription)
    formData.append(
      'day_of_week',
      new Date(selectedSession.session_date + 'T00:00:00').getDay() || 7
    )
    formData.append('session_date', selectedSession.session_date)
    formData.append('edit_scope', 'single')
    formData.append('recurring_weeks', '1')

    fetch(
      `http://127.0.0.1:8001/sessions/edit/${selectedSession.session_id}`,
      {
        method: 'PUT',
        body: formData,
      }
    )
      .then(async (response) => {
        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || `HTTP ${response.status}`)
        }

        return data
      })
      .then(() => {
        return fetch(
          `http://127.0.0.1:8001/sessions/api?week_offset=${weekOffset}`
        )
      })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then((freshData) => {
        setData(freshData)

        setSelectedSession({
          ...selectedSession,
          start: editStart,
          end: editEnd,
          description: editDescription,
        })

        setEditMode(false)
      })
      .catch((error) => {
        setError(error.message)
      })
  }

  if (selectedSession && editMode) {
    return (
      <main className="clients-page sessions-page">
        <button
          className="back-button"
          onClick={() => setEditMode(false)}
        >
          ← Anuluj
        </button>

        <h1>Edytuj sesję</h1>

        <div className="edit-form">
          <label>
            Godzina rozpoczęcia
            <input
              type="time"
              value={editStart}
              onChange={(event) => setEditStart(event.target.value)}
            />
          </label>

          <label>
            Godzina zakończenia
            <input
              type="time"
              value={editEnd}
              onChange={(event) => setEditEnd(event.target.value)}
            />
          </label>

          <label>
            Opis
            <textarea
              value={editDescription}
              onChange={(event) =>
                setEditDescription(event.target.value)
              }
            />
          </label>

          <button
            className="save-button"
            onClick={saveSession}
          >
            Zapisz
          </button>
        </div>
      </main>
    )
  }

  if (selectedSession) {
    return (
      <main className="clients-page sessions-page">
        <button
          className="back-button"
          onClick={() => setSelectedSession(null)}
        >
          ← Sesje
        </button>

        <h1>Szczegóły sesji</h1>

        <div className="client-details">
          <p>
            <strong>Klient:</strong> {selectedSession.client}
          </p>

          <p>
            <strong>Data:</strong> {selectedSession.session_date}
          </p>

          <p>
            <strong>Godziny:</strong> {selectedSession.start} – {selectedSession.end}
          </p>

          <p>
            <strong>Opis:</strong>{' '}
            {selectedSession.description || '—'}
          </p>

          <p>
            <strong>Cykliczna:</strong>{' '}
            {selectedSession.is_recurring ? 'Tak' : 'Nie'}
          </p>
        </div>

        <button
          className="edit-button"
          onClick={() => {
            setEditStart(selectedSession.start)
            setEditEnd(selectedSession.end)
            setEditDescription(selectedSession.description)
            setEditMode(true)
          }}
        >
          ✎ Edytuj
        </button>
      </main>
    )
  }

  return (
    <main className="clients-page sessions-page">
      <button className="back-button" onClick={onBack}>
        ← Klienci
      </button>

      <h1>Sesje</h1>

      <div className="week-navigation">
        <button
          className="week-button"
          onClick={() => setWeekOffset(weekOffset - 1)}
        >
          ←
        </button>

        <button
          className="today-button"
          onClick={() => setWeekOffset(0)}
        >
          Dzisiaj
        </button>

        <button
          className="week-button"
          onClick={() => setWeekOffset(weekOffset + 1)}
        >
          →
        </button>
      </div>

      {error && <p className="error">Błąd: {error}</p>}

      {!error && !data && <p>Ładowanie...</p>}

      {data && (
        <>
          <p className="week-info">
            Tydzień od: <strong>{data.week_start}</strong>
          </p>

          <div className="sessions-table-wrap">
            <table className="sessions-table">
              <thead>
                <tr>
                  <th>Godz.</th>

                  {days.map((day) => (
                    <th
                      key={day}
                      className={
                        data.current_day === day && weekOffset === 0
                          ? 'today-column'
                          : ''
                      }
                    >
                      {data.days[day]}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="empty-sessions">
                      Brak sesji w tym tygodniu
                    </td>
                  </tr>
                ) : (
                  rows.map(([time, daySessions]) => (
                    <tr key={time}>
                      <td className="session-time">{time}</td>

                      {days.map((day) => {
                        const session = daySessions[String(day)]

                        return (
                          <td
                            key={day}
                            className={
                              session?.is_live
                                ? 'session-cell live-session'
                                : 'session-cell'
                            }
                          >
                            {session && (
                              <div
                                  className="session-card"
                                  onClick={() => setSelectedSession(session)}
                                >
                                <strong>{session.client}</strong>

                                {session.description && (
                                  <span>
                                    {session.description}
                                  </span>
                                )}

                                {session.is_recurring && (
                                  <small>🔁</small>
                                )}
                              </div>
                            )}
                          </td>
                        )
                      })}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  )
}

export default Sessions
