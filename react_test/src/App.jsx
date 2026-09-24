import { useEffect, useState } from 'react'
import './App.css'
import Sessions from './Sessions'

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
  })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    setError('')

    fetch(`http://127.0.0.1:8001/clients/list?active=${active}`)
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

  function openClient(clientId) {
    setError('')
    setMessage('')
    setEditMode(false)

    fetch(`http://127.0.0.1:8001/clients/${clientId}`)
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

    fetch('http://127.0.0.1:8001/clients/create', {
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
          `http://127.0.0.1:8001/clients/list?active=${active}`
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

    fetch(`http://127.0.0.1:8001/clients/edit/${selectedClient.Id}`, {
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

        return fetch(
          `http://127.0.0.1:8001/clients/${selectedClient.Id}`
        )
      })
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

  const filteredClients = clients.filter((client) => {
    const text = `${client.FirstName} ${client.LastName}`.toLowerCase()

    return text.includes(search.toLowerCase())
  })

  if (page === 'sessions') {
    return <Sessions onBack={() => setPage('clients')} />
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
            <strong>Telefon:</strong> {selectedClient.Phone || '—'}
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
