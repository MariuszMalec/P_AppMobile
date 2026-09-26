import { useEffect, useState } from 'react'
import './App.css'
import API_URL from './api'

function App() {
  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [filterName, setFilterName] = useState('')
  const [filterTrophy, setFilterTrophy] = useState('')
  const [filterResult, setFilterResult] = useState('')
  const [sort, setSort] = useState('')

  const [selectedTeam, setSelectedTeam] = useState(null)
  const [teamPicture, setTeamPicture] = useState('')
  const [pictureLoading, setPictureLoading] = useState(false)

  const [trophiesTeam, setTrophiesTeam] = useState(null)
  const [teamTrophies, setTeamTrophies] = useState([])
  const [trophiesLoading, setTrophiesLoading] = useState(false)

  const [editTeamOpen, setEditTeamOpen] = useState(false)
  const [editTeam, setEditTeam] = useState(null)
  const [editTeamError, setEditTeamError] = useState('')

  const [createTeamOpen, setCreateTeamOpen] = useState(false)
  const [createTeamError, setCreateTeamError] = useState('')
  const [trophyOptions, setTrophyOptions] = useState([])

  const [createTeamForm, setCreateTeamForm] = useState({
    Name: '',
    Description: 'Example description',
    NationalityName: 'Unknown',
    Season: 2026,
    TopScorer: 'John Doe',
    FinalResult: '2nd place',
    TrophyModelId: '',
    Picture: 'http://127.0.0.1:8001/static/images/Team_2026.png',
  })

  const loadTeams = () => {
    setLoading(true)
    setError('')

    const params = new URLSearchParams()

    if (filterName.trim()) {
      params.set('filter_name', filterName.trim())
    }

    if (filterTrophy.trim()) {
      params.set('filter_trophy', filterTrophy.trim())
    }

    if (filterResult.trim()) {
      params.set('filter_result', filterResult.trim())
    }

    if (sort) {
      params.set('sort', sort)
    }

    const query = params.toString()
    const url = `${API_URL}/api/teams${query ? `?${query}` : ''}`

    fetch(url)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then(data => {
        setTeams(data)
        setLoading(false)
      })
      .catch(error => {
        setError(error.message)
        setLoading(false)
      })
  }

  useEffect(() => {
    loadTeams()
  }, [filterName, filterTrophy, filterResult, sort])

  const clearFilters = () => {
    setFilterName('')
    setFilterTrophy('')
    setFilterResult('')
    setSort('')
  }

  const openEditTeam = (team) => {
    setEditTeamError('')
    setEditTeam({
      ...team,
      Season: team.Season ?? '',
      FinalResult: team.FinalResult ?? '',
      TrophyModelId: team.TrophyModelId ?? '',
    })
    setEditTeamOpen(true)

    fetch(`${API_URL}/teams/trophies/options`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        return response.json()
      })
      .then(data => {
        setTrophyOptions(data)
      })
      .catch(() => {
        setTrophyOptions([])
        setEditTeamError('Nie można pobrać listy pucharów')
      })
  }

  const deleteTeam = (team) => {
    const confirmed = window.confirm(
      `Czy na pewno usunąć drużynę "${team.Name}"?`
    )

    if (!confirmed) {
      return
    }

    fetch(`${API_URL}/api/teams/${team.Id}`, {
      method: 'DELETE',
    })
      .then(async response => {
        const data = await response.json()

        if (!response.ok) {
          throw new Error(
            data.detail || `HTTP ${response.status}`
          )
        }

        return data
      })
      .then(() => {
        loadTeams()
      })
      .catch(error => {
        window.alert(`Nie udało się usunąć drużyny: ${error.message}`)
      })
  }

  const saveEditTeam = () => {
    setEditTeamError('')

    const payload = {
      ...editTeam,
      Season: Number(editTeam.Season),
      TrophyModelId: editTeam.TrophyModelId
        ? Number(editTeam.TrophyModelId)
        : null,
    }

    fetch(`${API_URL}/api/teams/${editTeam.Id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
      .then(async response => {
        const data = await response.json()

        if (!response.ok) {
          throw new Error(
            data.detail || `HTTP ${response.status}`
          )
        }

        return data
      })
      .then(() => {
        closeEditTeam()
        loadTeams()
      })
      .catch(error => {
        setEditTeamError(error.message)
      })
  }

  const closeEditTeam = () => {
    setEditTeamOpen(false)
    setEditTeam(null)
    setEditTeamError('')
  }

  const openTeamPicture = (team) => {
    setSelectedTeam(team)
    setTeamPicture('')
    setPictureLoading(true)

    fetch(`${API_URL}/teams/${team.Id}/picture`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then(data => {
        setTeamPicture(data.picture || '')
        setPictureLoading(false)
      })
      .catch(() => {
        setTeamPicture('')
        setPictureLoading(false)
      })
  }

  const closeTeamPicture = () => {
    setSelectedTeam(null)
    setTeamPicture('')
  }

  const openTeamTrophies = (team) => {
    setTrophiesTeam(team)
    setTeamTrophies([])
    setTrophiesLoading(true)

    fetch(`${API_URL}/api/teams/${team.Id}/trophies_by_season`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then(data => {
        setTeamTrophies(data)
        setTrophiesLoading(false)
      })
      .catch(() => {
        setTeamTrophies([])
        setTrophiesLoading(false)
      })
  }

  const closeTeamTrophies = () => {
    setTrophiesTeam(null)
    setTeamTrophies([])
  }

  const openCreateTeam = () => {
    setCreateTeamError('')

    fetch(`${API_URL}/teams/trophies/options`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then(data => {
        setTrophyOptions(data)
        setCreateTeamOpen(true)
      })
      .catch(() => {
        setTrophyOptions([])
        setCreateTeamError('Nie można pobrać listy pucharów')
        setCreateTeamOpen(true)
      })
  }

  const closeCreateTeam = () => {
    setCreateTeamOpen(false)
    setCreateTeamError('')
  }

  const createTeam = () => {
    setCreateTeamError('')

    const payload = {
      ...createTeamForm,
      Season: Number(createTeamForm.Season),
      TrophyModelId: createTeamForm.TrophyModelId
        ? Number(createTeamForm.TrophyModelId)
        : null,
    }

    fetch(`${API_URL}/api/teams`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
      .then(async response => {
        const data = await response.json()

        if (!response.ok) {
          throw new Error(
            data.detail || `HTTP ${response.status}`
          )
        }

        return data
      })
      .then(() => {
        closeCreateTeam()
        loadTeams()
      })
      .catch(error => {
        setCreateTeamError(error.message)
      })
  }

  const getImageUrl = (picture) => {
    if (!picture) {
      return ''
    }

    if (picture.startsWith('http')) {
      return picture
    }

    return `${API_URL}${picture}`
  }

  return (
    <div className="app">

      <nav className="navbar">
        <div className="navbar-brand">
          🏆 Sports Manager
        </div>

        <div className="nav-buttons">
          <button>Home</button>
          <button className="active">Teams</button>
          <button>Trophies</button>
        </div>
      </nav>

      <main className="content">

        <div className="page-header">
          <div>
            <h1>🏟️ Teams</h1>
            <p className="result-count">
              {loading ? 'Ładowanie...' : `${teams.length} wyników`}
            </p>
          </div>

          <button
            className="create-team-button"
            onClick={openCreateTeam}
          >
            + Create Team
          </button>
        </div>

        <div className="filters">

          <input
            type="text"
            placeholder="Nazwa drużyny"
            value={filterName}
            onChange={event => setFilterName(event.target.value)}
          />

          <input
            type="text"
            placeholder="Puchar"
            value={filterTrophy}
            onChange={event => setFilterTrophy(event.target.value)}
          />

          <input
            type="text"
            placeholder="Final Result"
            value={filterResult}
            onChange={event => setFilterResult(event.target.value)}
          />

          <select
            value={sort}
            onChange={event => setSort(event.target.value)}
          >
            <option value="">Sortowanie</option>
            <option value="name_asc">Nazwa ↑</option>
            <option value="name_desc">Nazwa ↓</option>
            <option value="season_asc">Sezon ↑</option>
            <option value="season_desc">Sezon ↓</option>
          </select>

          <button
            className="clear-button"
            onClick={clearFilters}
          >
            Wyczyść
          </button>

        </div>

        {loading && (
          <div className="message">
            Ładowanie drużyn...
          </div>
        )}

        {error && (
          <div className="message error">
            BŁĄD: {error}
          </div>
        )}

        {!loading && !error && (
          <div className="table-card">
            <div className="table-wrapper">

              <table className="teams-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Season</th>
                    <th>Final Result</th>
                    <th>Trophy</th>
                  </tr>
                </thead>

                <tbody>
                  {teams.map(team => (
                    <tr key={team.Id}>

                      <td>
                      <button
                        className="team-name-button"
                        onClick={() => openTeamPicture(team)}
                      >
                        {team.Name}
                      </button>

                      <div className="team-actions">
                        <button
                          className="team-edit-button"
                          onClick={() => openEditTeam(team)}
                        >
                          ✏️
                        </button>

                        <button
                          className="team-delete-button"
                          onClick={() => deleteTeam(team)}
                        >
                          🗑
                        </button>
                      </div>
                    </td>

                      <td>
                        {team.Season}
                      </td>

                      <td>
                        <span className="result">
                          {team.FinalResult || '-'}
                        </span>
                      </td>

                      <td>
                        <button
                          className="trophy-cell trophy-cell-button"
                          onClick={() => openTeamTrophies(team)}
                        >

                          {team.TrophyPicture && (
                            <img
                              src={getImageUrl(team.TrophyPicture)}
                              alt=""
                              className="trophy-picture"
                            />
                          )}

                          <span>
                            {team.TrophyWin || 'No'}
                          </span>

                        </button>
                      </td>

                    </tr>
                  ))}
                </tbody>
              </table>

            </div>
          </div>
        )}

      </main>

      <footer>
        © 2026 Sports Manager • React + FastAPI
      </footer>

      {trophiesTeam && (
        <div
          className="modal-backdrop"
          onClick={closeTeamTrophies}
        >
          <div
            className="team-modal trophies-modal"
            onClick={event => event.stopPropagation()}
          >

            <button
              className="modal-close"
              onClick={closeTeamTrophies}
            >
              ×
            </button>

            <h2>
              {trophiesTeam.Name} — Trophies by Season
            </h2>

            {trophiesLoading && (
              <div className="modal-message">
                Ładowanie...
              </div>
            )}

            {!trophiesLoading && teamTrophies.length === 0 && (
              <div className="modal-message">
                Brak pucharów
              </div>
            )}

            {!trophiesLoading && teamTrophies.length > 0 && (
              <div className="trophies-by-season">

                {teamTrophies.map(season => (
                  <div
                    className="season-block"
                    key={season.Season}
                  >

                    <h3>
                      {season.Season}
                    </h3>

                    <div className="season-trophies">

                      {season.Trophies.map(trophy => (
                        <div
                          className="season-trophy"
                          key={trophy.Id}
                        >

                          {trophy.Picture && (
                            <img
                              src={getImageUrl(trophy.Picture)}
                              alt={trophy.Name}
                            />
                          )}

                          <div className="season-trophy-name">
                            {trophy.Name}
                          </div>

                          {trophy.Lose && trophy.LoserPicture && (
                            <img
                              src={getImageUrl(trophy.LoserPicture)}
                              alt="Loser"
                              className="loser-picture"
                            />
                          )}

                        </div>
                      ))}

                    </div>
                  </div>
                ))}

              </div>
            )}

          </div>
        </div>
      )}

      {editTeamOpen && editTeam && (
        <div
          className="modal-backdrop"
          onClick={closeEditTeam}
        >
          <div
            className="team-modal create-team-modal"
            onClick={event => event.stopPropagation()}
          >
            <button
              className="modal-close"
              onClick={closeEditTeam}
            >
              ×
            </button>

            <h2>Edit Team</h2>

            {editTeamError && (
              <div className="create-team-error">
                ⚠️ {editTeamError}
              </div>
            )}

            <div className="create-team-form">

              <label>
                Name *
                <input
                  value={editTeam.Name || ''}
                  onChange={event =>
                    setEditTeam({
                      ...editTeam,
                      Name: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Description
                <input
                  value={editTeam.Description || ''}
                  onChange={event =>
                    setEditTeam({
                      ...editTeam,
                      Description: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Nationality *
                <input
                  value={editTeam.NationalityName || ''}
                  onChange={event =>
                    setEditTeam({
                      ...editTeam,
                      NationalityName: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Season
                <input
                  type="number"
                  value={editTeam.Season}
                  onChange={event =>
                    setEditTeam({
                      ...editTeam,
                      Season: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Top Scorer
                <input
                  value={editTeam.TopScorer || ''}
                  onChange={event =>
                    setEditTeam({
                      ...editTeam,
                      TopScorer: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Final Result
                <input
                  value={editTeam.FinalResult || ''}
                  onChange={event =>
                    setEditTeam({
                      ...editTeam,
                      FinalResult: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Trophy Win
                <select
                  value={editTeam.TrophyModelId || ''}
                  onChange={event =>
                    setEditTeam({
                      ...editTeam,
                      TrophyModelId: event.target.value
                    })
                  }
                >
                  <option value="">No</option>

                  {trophyOptions.map(trophy => (
                    <option
                      key={trophy.Id}
                      value={trophy.Id}
                    >
                      {trophy.Name}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Trophy Model ID
                <input
                  type="number"
                  value={editTeam.TrophyModelId || ''}
                  readOnly
                />
              </label>

              <label>
                Picture (URL or filename)
                <input
                  value={editTeam.Picture || ''}
                  onChange={event =>
                    setEditTeam({
                      ...editTeam,
                      Picture: event.target.value
                    })
                  }
                />
              </label>

            </div>

            <div className="create-team-footer">

              <button
                type="button"
                className="create-team-cancel"
                onClick={closeEditTeam}
              >
                Cancel
              </button>

              <button
                type="button"
                className="create-team-submit"
                onClick={saveEditTeam}
              >
                Save
              </button>

            </div>

          </div>
        </div>
      )}

      {createTeamOpen && (
        <div
          className="modal-backdrop"
          onClick={closeCreateTeam}
        >
          <div
            className="team-modal create-team-modal"
            onClick={event => event.stopPropagation()}
          >

            <button
              className="modal-close"
              onClick={closeCreateTeam}
            >
              ×
            </button>

            <h2>Create Team</h2>

            {createTeamError && (
              <div className="create-team-error">
                ⚠️ {createTeamError}
              </div>
            )}

            <div className="create-team-form">

              <label>
                Name *
                <input
                  value={createTeamForm.Name}
                  onChange={event =>
                    setCreateTeamForm({
                      ...createTeamForm,
                      Name: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Description
                <input
                  value={createTeamForm.Description}
                  onChange={event =>
                    setCreateTeamForm({
                      ...createTeamForm,
                      Description: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Nationality *
                <input
                  value={createTeamForm.NationalityName}
                  onChange={event =>
                    setCreateTeamForm({
                      ...createTeamForm,
                      NationalityName: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Season
                <input
                  type="number"
                  value={createTeamForm.Season}
                  onChange={event =>
                    setCreateTeamForm({
                      ...createTeamForm,
                      Season: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Top Scorer
                <input
                  value={createTeamForm.TopScorer}
                  onChange={event =>
                    setCreateTeamForm({
                      ...createTeamForm,
                      TopScorer: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Final Result
                <input
                  value={createTeamForm.FinalResult}
                  onChange={event =>
                    setCreateTeamForm({
                      ...createTeamForm,
                      FinalResult: event.target.value
                    })
                  }
                />
              </label>

              <label>
                Trophy Win
                <select
                  value={createTeamForm.TrophyModelId}
                  onChange={event =>
                    setCreateTeamForm({
                      ...createTeamForm,
                      TrophyModelId: event.target.value
                    })
                  }
                >
                  <option value="">No</option>

                  {trophyOptions.map(trophy => (
                    <option
                      key={trophy.Id}
                      value={trophy.Id}
                    >
                      {trophy.Name}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Trophy Model ID
                <input
                  type="number"
                  value={createTeamForm.TrophyModelId}
                  readOnly
                />
              </label>

              <label>
                Picture (URL or filename)
                <input
                  value={createTeamForm.Picture}
                  onChange={event =>
                    setCreateTeamForm({
                      ...createTeamForm,
                      Picture: event.target.value
                    })
                  }
                />
              </label>

            </div>

            <div className="create-team-footer">

              <button
                type="button"
                className="create-team-cancel"
                onClick={closeCreateTeam}
              >
                Cancel
              </button>

              <button
                type="button"
                className="create-team-submit"
                onClick={createTeam}
              >
                Create
              </button>

            </div>

          </div>
        </div>
      )}

      {selectedTeam && (
        <div
          className="modal-backdrop"
          onClick={closeTeamPicture}
        >
          <div
            className="team-modal"
            onClick={event => event.stopPropagation()}
          >

            <button
              className="modal-close"
              onClick={closeTeamPicture}
            >
              ×
            </button>

            <h2>{selectedTeam.Name}</h2>

            {pictureLoading && (
              <div className="modal-message">
                Ładowanie...
              </div>
            )}

            {!pictureLoading && teamPicture && (
              <img
                src={getImageUrl(teamPicture)}
                alt={selectedTeam.Name}
                className="team-modal-picture"
              />
            )}

            {!pictureLoading && !teamPicture && (
              <div className="modal-message">
                Brak zdjęcia
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  )
}

export default App
