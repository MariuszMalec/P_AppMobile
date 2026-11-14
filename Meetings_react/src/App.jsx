import { useEffect, useRef, useState } from 'react'
import API_URL from './api'
import './App.css'
import Sessions from './Sessions'
import { connectGoogleAccount, uploadAndShareBackup } from './googleDriveBackup'

function App() {
  const [clients, setClients] = useState([])
  const [selectedClient, setSelectedClient] = useState(null)
  const [search, setSearch] = useState('')
  const [active, setActive] = useState(1)
  const [editMode, setEditMode] = useState(false)
  const [createMode, setCreateMode] = useState(false)
  const [page, setPage] = useState('clients')
  const [newClient, setNewClient] = useState({
    FirstName: '',
    LastName: '',
    Age: null,
    Description: '',
    Phone: '',
    Gender: '',
    IsActive: 1,
    Color: '',
  })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const importFileRef = useRef(null)
  const [driveAccountEmail, setDriveAccountEmail] = useState(
    () => localStorage.getItem('meetingsDriveAccount') || ''
  )
  const [driveRecipient, setDriveRecipient] = useState(
    () => localStorage.getItem('meetingsDriveRecipient') || 'mario106c@gmail.com'
  )
  const [rememberDriveRecipient, setRememberDriveRecipient] = useState(
    () => localStorage.getItem('meetingsRememberDriveRecipient') !== 'false'
  )
  const [driveBusy, setDriveBusy] = useState(false)
  const nativeDriveResolveRef = useRef(null)
  const nativeDriveRejectRef = useRef(null)

  useEffect(() => {
    if (!window.AndroidBridge) return

    window.onAndroidDriveConnected = (email) => {
      setDriveAccountEmail(email)
      localStorage.setItem('meetingsDriveAccount', email)
      setMessage(`Połączono z Google: ${email}`)
      nativeDriveResolveRef.current?.(email)
      nativeDriveResolveRef.current = null
      nativeDriveRejectRef.current = null
    }

    window.onAndroidDriveBackupStatus = (status) => {
      setMessage(status)
    }

    window.onAndroidDriveBackupSuccess = (resultJson) => {
      let result = resultJson
      if (typeof resultJson === 'string') {
        try { result = JSON.parse(resultJson) } catch { result = {} }
      }
      setMessage(
        result?.updated
          ? 'Kopia na Google Drive została zaktualizowana i udostępniona.'
          : 'Kopia została wysłana na Google Drive i udostępniona.'
      )
      nativeDriveResolveRef.current?.(result)
      nativeDriveResolveRef.current = null
      nativeDriveRejectRef.current = null
      setDriveBusy(false)
    }

    window.onAndroidDriveBackupError = (message) => {
      setMessage('')
      setError(`Google Drive: ${message}`)
      nativeDriveRejectRef.current?.(new Error(message))
      nativeDriveResolveRef.current = null
      nativeDriveRejectRef.current = null
      setDriveBusy(false)
    }

    return () => {
      delete window.onAndroidDriveConnected
      delete window.onAndroidDriveBackupStatus
      delete window.onAndroidDriveBackupSuccess
      delete window.onAndroidDriveBackupError
    }
  }, [])

  useEffect(() => {
    if (!message) return
    const t = setTimeout(() => {
      setMessage('')
    }, 4000)
    return () => clearTimeout(t)
  }, [message])

  useEffect(() => {
    setError('')

    fetch(`${API_URL}/clients/list?active=${active}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then((data) => {
        setClients(data)
      })
      .catch((error) => {
        setError(error.message)
      })
  }, [active])

  function exportDatabase() {
    setError('')
    setMessage('')

    if (
      window.AndroidBridge &&
      typeof window.AndroidBridge.exportDatabase === 'function'
    ) {
      setMessage('Przygotowuję kopię bazy...')
      window.AndroidBridge.exportDatabase()
      return
    }

    fetch(`${API_URL}/api/backup/export`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        return response.blob()
      })
      .then((blob) => {
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        const timestamp = new Date()
          .toISOString()
          .replace(/[:.]/g, '-')

        link.href = url
        link.download = `meetings-backup-${timestamp}.db`
        document.body.appendChild(link)
        link.click()
        link.remove()
        URL.revokeObjectURL(url)
        setMessage('Kopia bazy została pobrana.')
      })
      .catch((err) => {
        setError(`Nie udało się wyeksportować bazy: ${err.message}`)
      })
  }

  async function importDatabase(event) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    setError('')
    setMessage('')

    if (!/\.db(\s*\(\d+\))?$/i.test(file.name)) {
      setError('Wybierz plik bazy danych z rozszerzeniem .db.')
      return
    }

    if (!window.confirm(
      'Import zastąpi obecną bazę klientów i sesji. ' +
      'Najpierw zostanie utworzona kopia bezpieczeństwa. Kontynuować?'
    )) return

    setMessage('Sprawdzam bazę i przygotowuję import...')
    try {
      const buffer = await file.arrayBuffer()
      const data = new FormData()
      data.append(
        'file',
        new Blob([buffer], { type: 'application/octet-stream' }),
        'import.db'
      )
      const response = await fetch(`${API_URL}/api/backup/import`, {
        method: 'POST',
        body: data,
      })
      const result = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`)

      setSelectedClient(null)
      setEditMode(false)
      setCreateMode(false)
      setSearch('')

      const listResponse = await fetch(`${API_URL}/clients/list?active=${active}`)
      if (!listResponse.ok) throw new Error(
        'Import wykonano, ale nie udało się odświeżyć listy klientów. Odśwież widok.'
      )
      setClients(await listResponse.json())
      setMessage(`Import zakończony. Kopia poprzedniej bazy: ${result.backup || 'utworzona'}.`)
    } catch (err) {
      setMessage('')
      setError(`Import: ${err.message}`)
      
      const log = [
      'MEETINGS - LOG BŁĘDU IMPORTU',
      '================================',
      `Data: ${new Date().toLocaleString()}`,
      `API: ${API_URL}`,
      '' ,
      'PLIK BAZY:',
      `Nazwa: ${file.name}`,
      `Rozmiar: ${file.size} bajtów`,
      `Typ: ${file.type || 'nieznany'}`,
      '' ,
      'BŁĄD:',
      `Nazwa błędu: ${err?.name || 'brak'}`,
      `Komunikat: ${err?.message || String(err)}`,
      '' ,
      'STACK:',
      err?.stack || 'Brak informacji',
      '' ,
      'PRZEGLĄDARKA:',
      navigator.userAgent,
      ].join('\n')
      
      const blob = new Blob([log], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `meetings-import-error-${Date.now()}.txt`
      document.body.appendChild(link)
      link.click()
      link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 2000)
      }
  }

  async function connectDrive() {
    setError('')
    setMessage('')
    setDriveBusy(true)

    try {
      if (window.AndroidBridge && typeof window.AndroidBridge.connectGoogleDrive === 'function') {
        await new Promise((resolve, reject) => {
          nativeDriveResolveRef.current = resolve
          nativeDriveRejectRef.current = reject
          window.AndroidBridge.connectGoogleDrive()
        })
        return
      }

      const email = await connectGoogleAccount()
      setDriveAccountEmail(email)
      localStorage.setItem('meetingsDriveAccount', email)
      setMessage(`Połączono z Google: ${email}`)
    } catch (err) {
      setError(`Google Drive: ${err.message}`)
    } finally {
      setDriveBusy(false)
    }
  }

  async function saveDriveRecipient(value) {
    setDriveRecipient(value)

    if (rememberDriveRecipient) {
      localStorage.setItem('meetingsDriveRecipient', value)
    }
  }

  function changeRememberDriveRecipient(checked) {
    setRememberDriveRecipient(checked)
    localStorage.setItem('meetingsRememberDriveRecipient', String(checked))

    if (checked) {
      localStorage.setItem('meetingsDriveRecipient', driveRecipient)
    } else {
      localStorage.removeItem('meetingsDriveRecipient')
    }
  }

  async function sendBackupToDrive() {
    setError('')
    setMessage('')
    setDriveBusy(true)

    try {
      if (rememberDriveRecipient) {
        localStorage.setItem('meetingsDriveRecipient', driveRecipient)
      }

      if (window.AndroidBridge && typeof window.AndroidBridge.uploadBackupToGoogleDrive === 'function') {
        await new Promise((resolve, reject) => {
          nativeDriveResolveRef.current = resolve
          nativeDriveRejectRef.current = reject
          window.AndroidBridge.uploadBackupToGoogleDrive(driveRecipient)
        })
        return
      }

      const result = await uploadAndShareBackup(
        driveRecipient,
        (status) => setMessage(status)
      )

      setMessage(
        result.updated
          ? 'Kopia na Google Drive została zaktualizowana i udostępniona.'
          : 'Kopia została wysłana na Google Drive i udostępniona.'
      )
    } catch (err) {
      setMessage('')
      setError(`Google Drive: ${err.message}`)
    } finally {
      setDriveBusy(false)
    }
  }

  function openClient(clientId) {
    setError('')
    setMessage('')
    setEditMode(false)

    fetch(`${API_URL}/clients/${clientId}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then((data) => {
        setSelectedClient(data)
      })
      .catch((error) => {
        setError(error.message)
      })
  }

  function backToClients() {
    setSelectedClient(null)
    setEditMode(false)
    setMessage('')
    setError('')
  }

  function startEdit() {
    setError('')
    setMessage('')
    setEditMode(true)
  }

  function createClient() {
    setError('')
    setMessage('')

    const formData = new FormData()

    formData.append('first_name', newClient.FirstName)
    formData.append('last_name', newClient.LastName)
    formData.append(
      'age',
      newClient.Age === null ? '' : newClient.Age
    )
    formData.append('description', newClient.Description)
    formData.append('phone', newClient.Phone)
    formData.append('gender', newClient.Gender)
    formData.append('is_active', newClient.IsActive ? '1' : '0')
    formData.append('color', newClient.Color || '')

    fetch(`${API_URL}/clients/create`, {
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
      .then((data) => {
        setMessage(data.message)
        setCreateMode(false)

        return fetch(
          `${API_URL}/clients/list?active=${active}`
        )
      })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then((data) => {
        setClients(data)

        setNewClient({
          FirstName: '',
          LastName: '',
          Age: null,
          Description: '',
          Phone: '',
          Gender: '',
          IsActive: 1,
    Color: '',
        })
      })
      .catch((error) => {
        setError(error.message)
      })
  }

  function saveClient() {
    setError('')
    setMessage('')

    const formData = new FormData()

    formData.append('first_name', selectedClient.FirstName)
    formData.append('last_name', selectedClient.LastName)
    formData.append(
      'age',
      selectedClient.Age === null ? '' : selectedClient.Age
    )
    formData.append('description', selectedClient.Description || '')
    formData.append('phone', selectedClient.Phone || '')
    formData.append('gender', selectedClient.Gender || '')
    formData.append('is_active', selectedClient.IsActive ? '1' : '0')
    formData.append('color', selectedClient.Color || '')

    fetch(`${API_URL}/clients/edit/${selectedClient.Id}`, {
      method: 'PUT',
      body: formData,
    })
      .then(async (response) => {
        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || `HTTP ${response.status}`)
        }

        return data
      })
      .then((data) => {
        setMessage(data.message)
        setEditMode(false)
        setSelectedClient(null)

        return fetch(
          `${API_URL}/clients/${selectedClient.Id}`
        )
      })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then((data) => {
        setSelectedClient(null)

        return fetch(`${API_URL}/clients/list?active=${active}`)
      })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then((data) => {
        setClients(data)
      })
      .catch((error) => {
        setError(error.message)
      })
  }

  const filteredClients = clients.filter((client) => {
    const text = `${client.FirstName} ${client.LastName}`.toLowerCase()

    return text.includes(search.toLowerCase())
  })

  if (page === 'sessions') {
    return <Sessions onBack={() => setPage('clients')} />
  }

  if (page === 'settings') {
    return (
      <main className="clients-page">
        <button
          className="back-button"
          onClick={() => setPage('clients')}
        >
          ← Klienci
        </button>

        <h1>Ustawienia</h1>

        {message && <p className="success">{message}</p>}
        {error && <p className="error">Błąd: {error}</p>}

        <h2>Kopia zapasowa Google Drive</h2>

        {driveAccountEmail && (
          <p>Połączone konto: <strong>{driveAccountEmail}</strong></p>
        )}

        <button
          className="new-client-button"
          onClick={connectDrive}
          disabled={driveBusy}
        >
          {driveAccountEmail ? 'Połącz inne konto Google' : 'Połącz z Google'}
        </button>

        <label>
          Adres e-mail odbiorcy kopii:
          <input
            type="email"
            value={driveRecipient}
            onChange={(event) => saveDriveRecipient(event.target.value)}
            placeholder="adres@gmail.com"
          />
        </label>

        <label>
          <input
            type="checkbox"
            checked={rememberDriveRecipient}
            onChange={(event) => changeRememberDriveRecipient(event.target.checked)}
          />
          Zapamiętaj adres odbiorcy
        </label>

        <button
          className="new-client-button"
          onClick={sendBackupToDrive}
          disabled={driveBusy || !driveAccountEmail}
        >
          {driveBusy ? 'Przetwarzanie...' : 'Wyślij kopię na Google Drive'}
        </button>

        <hr />
        <button
          className="new-client-button"
          onClick={exportDatabase}
        >
          ⬇ Eksportuj bazę
        </button>

        <button
          className="new-client-button"
          onClick={() => importFileRef.current?.click()}
        >
          ⬆ Importuj bazę
        </button>

        <input
          ref={importFileRef}
          type="file"
          accept=".db,application/octet-stream"
          onChange={importDatabase}
          style={{ display: 'none' }}
        />
      </main>
    )
  }


  if (createMode) {
    return (
      <main className="clients-page">
        <button
          className="back-button"
          onClick={() => setCreateMode(false)}
        >
          ← Anuluj
        </button>

        <h1>Nowy klient</h1>

        <div className="edit-form">
          <label>
            Imię
            <input
              type="text"
              value={newClient.FirstName}
              onChange={(event) =>
                setNewClient({
                  ...newClient,
                  FirstName: event.target.value,
                })
              }
            />
          </label>

          <label>
            Nazwisko
            <input
              type="text"
              value={newClient.LastName}
              onChange={(event) =>
                setNewClient({
                  ...newClient,
                  LastName: event.target.value,
                })
              }
            />
          </label>

          <label>
            Wiek
            <input
              type="number"
              value={newClient.Age ?? ''}
              onChange={(event) =>
                setNewClient({
                  ...newClient,
                  Age:
                    event.target.value === ''
                      ? null
                      : Number(event.target.value),
                })
              }
            />
          </label>

          <label>
            Telefon
            <input
              type="text"
              value={newClient.Phone}
              onChange={(event) =>
                setNewClient({
                  ...newClient,
                  Phone: event.target.value,
                })
              }
            />
          </label>

          <label>
            Opis
            <textarea
              value={newClient.Description}
              onChange={(event) =>
                setNewClient({
                  ...newClient,
                  Description: event.target.value,
                })
              }
            />
          </label>

          <label>
            Płeć
            <select
              value={newClient.Gender}
              onChange={(event) =>
                setNewClient({
                  ...newClient,
                  Gender: event.target.value,
                })
              }
            >
              <option value="">Wybierz płeć</option>
              <option value="male">Mężczyzna</option>
              <option value="female">Kobieta</option>
              <option value="other">Inna</option>
            </select>
          </label>

          <label>
            Kolor
            <input
              type="color"
              value={newClient.Color || '#3b82f6'}
              onChange={(event) =>
                setNewClient({ ...newClient, Color: event.target.value })
              }
            />
          </label>

          <label className="active-checkbox">
            <input
              type="checkbox"
              checked={Boolean(newClient.IsActive)}
              onChange={(event) =>
                setNewClient({
                  ...newClient,
                  IsActive: event.target.checked ? 1 : 0,
                })
              }
            />
            Aktywny
          </label>

          <button className="save-button" onClick={createClient}>
            Utwórz
          </button>
        </div>

        {error && <p className="error">Błąd: {error}</p>}
      </main>
    )
  }

  if (selectedClient && editMode) {
    return (
      <main className="clients-page">
        <button
          className="back-button"
          onClick={() => setEditMode(false)}
        >
          ← Anuluj
        </button>

        <h1>Edytuj klienta</h1>

        <div className="edit-form">
          <label>
            Imię
            <input
              type="text"
              value={selectedClient.FirstName}
              onChange={(event) =>
                setSelectedClient({
                  ...selectedClient,
                  FirstName: event.target.value,
                })
              }
            />
          </label>

          <label>
            Nazwisko
            <input
              type="text"
              value={selectedClient.LastName}
              onChange={(event) =>
                setSelectedClient({
                  ...selectedClient,
                  LastName: event.target.value,
                })
              }
            />
          </label>

          <label>
            Wiek
            <input
              type="number"
              value={selectedClient.Age ?? ''}
              onChange={(event) =>
                setSelectedClient({
                  ...selectedClient,
                  Age:
                    event.target.value === ''
                      ? null
                      : Number(event.target.value),
                })
              }
            />
          </label>

          <label>
            Telefon
            <input
              type="text"
              value={selectedClient.Phone || ''}
              onChange={(event) =>
                setSelectedClient({
                  ...selectedClient,
                  Phone: event.target.value,
                })
              }
            />
          </label>

          <label>
            Opis
            <textarea
              value={selectedClient.Description || ''}
              onChange={(event) =>
                setSelectedClient({
                  ...selectedClient,
                  Description: event.target.value,
                })
              }
            />
          </label>

          <label>
            Płeć
            <select
              value={selectedClient.Gender || ''}
              onChange={(event) =>
                setSelectedClient({
                  ...selectedClient,
                  Gender: event.target.value,
                })
              }
            >
              <option value="">Wybierz płeć</option>
              <option value="male">Mężczyzna</option>
              <option value="female">Kobieta</option>
              <option value="other">Inna</option>
            </select>
          </label>

          <label>
            Kolor
            <input
              type="color"
              value={selectedClient.Color || '#3b82f6'}
              onChange={(event) =>
                setSelectedClient({ ...selectedClient, Color: event.target.value })
              }
            />
          </label>

          <label className="active-checkbox">
            <input
              type="checkbox"
              checked={Boolean(selectedClient.IsActive)}
              onChange={(event) =>
                setSelectedClient({
                  ...selectedClient,
                  IsActive: event.target.checked ? 1 : 0,
                })
              }
            />
            Aktywny
          </label>

          <button className="save-button" onClick={saveClient}>
            Zapisz
          </button>
        </div>

        {error && <p className="error">Błąd: {error}</p>}
      </main>
    )
  }

  if (selectedClient) {
    return (
      <main className="clients-page">
        <button className="back-button" onClick={backToClients}>
          ← Wróć
        </button>

        <h1>
          {selectedClient.FirstName} {selectedClient.LastName}
        </h1>

        <button className="edit-button" onClick={startEdit}>
          ✎ Edytuj
        </button>

        {message && <p className="success">{message}</p>}

        <div className="client-details">
          <p>
            <strong>Wiek:</strong> {selectedClient.Age}
          </p>

          <p>
            <strong>Telefon:</strong>{' '}
            {selectedClient.Phone ? (
              <span className="phone-actions">
                {selectedClient.Phone}
                <a
                  className="phone-btn"
                  href={`tel:${String(selectedClient.Phone).replace(/[^\d+]/g, '')}`}
                >
                  📞 Zadzwoń
                </a>
                <a
                  className="phone-btn"
                  href={`sms:${String(selectedClient.Phone).replace(/[^\d+]/g, '')}`}
                >
                  💬 SMS
                </a>
              </span>
            ) : (
              '—'
            )}
          </p>

          <p>
            <strong>Opis:</strong> {selectedClient.Description || '—'}
          </p>

          <p>
            <strong>Płeć:</strong> {selectedClient.Gender}
          </p>

          <p>
            <strong>Aktywny:</strong>{' '}
            {selectedClient.IsActive ? 'Tak' : 'Nie'}
          </p>
        </div>

        {error && <p className="error">Błąd: {error}</p>}
      </main>
    )
  }

  return (
    <main className="clients-page">
        {message && <p className="success">{message}</p>}
      <h1>Klienci</h1>

      <button
        className="new-client-button"
        onClick={() => setPage('sessions')}
      >
        📅 Sesje
      </button>

      <button
        className="new-client-button"
        onClick={() => {
          setError('')
          setMessage('')
          setCreateMode(true)
        }}
      >
        + Nowy klient
      </button>

      <button
        className="new-client-button"
        onClick={() => {
          setError('')
          setMessage('')
          setPage('settings')
        }}
      >
        ⚙ Ustawienia
      </button>

      <div className="active-filter">
        <button
          className={
            active === 1
              ? 'active-filter-button selected'
              : 'active-filter-button'
          }
          onClick={() => setActive(1)}
        >
          Aktywni
        </button>

        <button
          className={
            active === 0
              ? 'active-filter-button selected'
              : 'active-filter-button'
          }
          onClick={() => setActive(0)}
        >
          Nieaktywni
        </button>
      </div>

      <input
        className="search-input"
        type="text"
        placeholder="Szukaj imienia lub nazwiska..."
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />

      {error && <p className="error">Błąd: {error}</p>}

      {!error && clients.length === 0 && (
        <p>Ładowanie...</p>
      )}

      {!error && clients.length > 0 && filteredClients.length === 0 && (
        <p>Nie znaleziono klienta.</p>
      )}

      <div className="clients-list">
        {filteredClients.map((client) => (
          <button
            className="client-row"
            key={client.Id}
            onClick={() => openClient(client.Id)}
          >
            <span>
              {client.FirstName} {client.LastName}
            </span>

            <span className="arrow">›</span>
          </button>
        ))}
      </div>
    </main>
  )
}

export default App

