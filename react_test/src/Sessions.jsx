import { useEffect, useState } from 'react'

function Sessions({ onBack }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [weekOffset, setWeekOffset] = useState(0)
  const [selectedSession, setSelectedSession] = useState(null)
  const [editMode, setEditMode] = useState(false)
  const [editStart, setEditStart] = useState('')
  const [editEnd, setEditEnd] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editDate, setEditDate] = useState('')
  const [editScope, setEditScope] = useState('single')
  const [editSeriesCount, setEditSeriesCount] = useState(1)
  const [createMode, setCreateMode] = useState(false)
  const [createStart, setCreateStart] = useState('')
  const [createEnd, setCreateEnd] = useState('')
  const [createClientId, setCreateClientId] = useState('')
  const [createDescription, setCreateDescription] = useState('')
  const [createDate, setCreateDate] = useState('')
  const [createRecurring, setCreateRecurring] = useState(false)
  const [createSeriesCount, setCreateSeriesCount] = useState(2)
  const [deleteMode, setDeleteMode] = useState(false)
  const [deleteScope, setDeleteScope] = useState('single')

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
      new Date(editDate + 'T00:00:00').getDay() || 7
    )
    formData.append('session_date', editDate)
    formData.append('edit_scope', editScope)
    formData.append(
      'recurring_weeks',
      editScope === 'series'
        ? String(editSeriesCount - 1)
        : '1'
    )

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

        setMessage(
          editScope === 'series'
            ? 'Seria została zmieniona'
            : 'Sesja została zmieniona'
        )

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

  function deleteSession(scope) {
    setError('')

    const formData = new FormData()
    formData.append('delete_scope', scope)

    fetch(
      `http://127.0.0.1:8001/sessions/delete/${selectedSession.session_id}`,
      {
        method: 'POST',
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
      .then(() =>
        fetch(
          `http://127.0.0.1:8001/sessions/api?week_offset=${weekOffset}`
        )
      )
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then((freshData) => {
        setData(freshData)
        setMessage(
          scope === 'series'
            ? 'Cała seria została usunięta'
            : 'Sesja usunięta'
        )
        setSelectedSession(null)
        setDeleteMode(false)
        setDeleteScope('single')
      })
      .catch((error) => setError(error.message))
  }

  function createSession() {
    setError('')

    if (!createDate) {
      setError('Wybierz datę')
      return
    }

    if (!createClientId) {
      setError('Wybierz klienta')
      return
    }

    if (!createStart) {
      setError('Wybierz godzinę rozpoczęcia')
      return
    }

    if (!createEnd) {
      setError('Wybierz godzinę zakończenia')
      return
    }

    if (createEnd <= createStart) {
      setError('Godzina zakończenia musi być późniejsza od rozpoczęcia')
      return
    }

    if (createRecurring && (createSeriesCount < 2 || createSeriesCount > 53)) {
      setError('Liczba sesji w serii musi być od 2 do 53')
      return
    }

    const formData = new FormData()

    formData.append('start', createStart)
    formData.append('end', createEnd)
    formData.append('client_id', createClientId)
    formData.append('description', createDescription)
    formData.append(
      'day_of_week',
      new Date(createDate + 'T00:00:00').getDay() || 7
    )
    formData.append('session_date', createDate)
    formData.append('recurring', createRecurring ? 'true' : 'false')
    formData.append(
      'recurring_weeks',
      createRecurring
        ? String(createSeriesCount - 1)
        : '0'
    )

    fetch('http://127.0.0.1:8001/sessions/create', {
      method: 'POST',
      body: formData,
    })
      .then(async (response) => {
        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || `HTTP ${response.status}`)
        }

        return data
      })
      .then(() =>
        fetch(
          `http://127.0.0.1:8001/sessions/api?week_offset=${weekOffset}`
        )
      )
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then((freshData) => {
        setData(freshData)
        setMessage(
          createRecurring
            ? 'Seria została dodana'
            : 'Sesja została dodana'
        )
        setCreateMode(false)
      })
      .catch((error) => setError(error.message))
  }

  if (createMode) {
    return (
      <main className="clients-page sessions-page">
        <button
          className="back-button"
          onClick={() => setCreateMode(false)}
        >
          ← Anuluj
        </button>

        <h1>Dodaj sesję</h1>

        {error && <p className="error">Błąd: {error}</p>}

        <div className="edit-form">
          <label>
            Data
            <input
              type="date"
              value={createDate}
              onChange={(event) => setCreateDate(event.target.value)}
            />
          </label>

          <label>
            Klient
            <select
              value={createClientId}
              onChange={(event) => setCreateClientId(event.target.value)}
            >
              <option value="">Wybierz klienta</option>
              {data.clients
                .filter((client) => client.Id)
                .map((client) => (
                  <option key={client.Id} value={client.Id}>
                    {client.FirstName} {client.LastName}
                  </option>
                ))}
            </select>
          </label>

          <label>
            Godzina rozpoczęcia
            <input
              type="time"
              value={createStart}
              onChange={(event) => setCreateStart(event.target.value)}
            />
          </label>

          <label>
            Godzina zakończenia
            <input
              type="time"
              value={createEnd}
              onChange={(event) => setCreateEnd(event.target.value)}
            />
          </label>

          <label>
            Opis
            <textarea
              value={createDescription}
              onChange={(event) => setCreateDescription(event.target.value)}
            />
          </label>

          <label>
            <input
              type="checkbox"
              checked={createRecurring}
              onChange={(event) => setCreateRecurring(event.target.checked)}
            />
            {' '}Sesja cykliczna
          </label>

          {createRecurring && (
            <label>
              Liczba sesji w serii
              <input
                type="number"
                min="2"
                max="53"
                value={createSeriesCount}
                onChange={(event) =>
                  setCreateSeriesCount(Number(event.target.value))
                }
              />
            </label>
          )}

          <button
            className="save-button"
            onClick={createSession}
          >
            Zapisz
          </button>
        </div>
      </main>
    )
  }

  if (selectedSession && deleteMode) {
    return (
      <main className="clients-page sessions-page">
        <button
          className="back-button"
          onClick={() => setDeleteMode(false)}
        >
          ← Anuluj
        </button>

        <h1>Usuń sesję</h1>

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

          {selectedSession.is_recurring ? (
            <>
              <p>
                Ta sesja należy do serii cyklicznej.
              </p>

              <button
                className="delete-button"
                onClick={() => {
                  setDeleteScope('single')
                  deleteSession('single')
                }}
              >
                Usuń tylko tę sesję
              </button>

              <button
                className="delete-button"
                onClick={() => {
                  setDeleteScope('series')
                  deleteSession('series')
                }}
              >
                Usuń całą serię
              </button>
            </>
          ) : (
            <button
              className="delete-button"
              onClick={() => {
                setDeleteScope('single')
                deleteSession('single')
              }}
            >
              Usuń sesję
            </button>
          )}

          {deleteScope && (
            <p>
              Wybrano:{' '}
              <strong>
                {deleteScope === 'series'
                  ? 'całą serię'
                  : 'tylko tę sesję'}
              </strong>
            </p>
          )}
        </div>
      </main>
    )
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
            Data
            <input
              type="date"
              value={editDate}
              onChange={(event) => setEditDate(event.target.value)}
            />
          </label>

          {selectedSession.is_recurring && (
            <label>
              Zakres edycji
              <select
                value={editScope}
                onChange={(event) => setEditScope(event.target.value)}
              >
                <option value="single">Tylko tę sesję</option>
                <option value="series">Całą serię</option>
              </select>
            </label>
          )}

          {selectedSession.is_recurring && editScope === 'series' && (
            <label>
              Liczba sesji w serii
              <input
                type="number"
                min="1"
                max="53"
                value={editSeriesCount}
                onChange={(event) =>
                  setEditSeriesCount(Number(event.target.value))
                }
              />
            </label>
          )}

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
            setEditDate(selectedSession.session_date)
            setEditScope('single')

            if (selectedSession.is_recurring) {
              fetch(
                `http://127.0.0.1:8001/sessions/recurring-count/${selectedSession.recurring_group_id}`
              )
                .then((response) => {
                  if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`)
                  }

                  return response.json()
                })
                .then((data) => {
                  setEditSeriesCount(data.count)
                })
                .catch((error) => {
                  setError(error.message)
                })
            } else {
              setEditSeriesCount(1)
            }

            setEditMode(true)
          }}
        >
          ✎ Edytuj
        </button>

        <button
          className="delete-button"
          onClick={() => {
            setDeleteScope('single')
            setDeleteMode(true)
          }}
        >
          🗑 Usuń
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

      <button
        className="edit-button"
        onClick={() => {
          setCreateStart('')
          setCreateEnd('')
          setCreateClientId('')
          setCreateDescription('')
          setCreateDate('')
          setCreateRecurring(false)
          setCreateSeriesCount(2)
          setError('')
          setCreateMode(true)
        }}
      >
        + Dodaj sesję
      </button>


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

      {message && <p className="success">{message}</p>}
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
