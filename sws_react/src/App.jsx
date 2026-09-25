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
