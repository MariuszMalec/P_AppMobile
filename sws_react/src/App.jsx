import { useEffect, useState } from 'react'
import './App.css'
import API_URL from './api'

function App() {
  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API_URL}/api/teams`)
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
  }, [])

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
                        <div className="team-name">
                          <span>{team.Name}</span>
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
                        <div className="trophy-cell">

                          {team.TrophyPicture && (
                            <img
                              src={
                                team.TrophyPicture.startsWith('http')
                                  ? team.TrophyPicture
                                  : `${API_URL}${team.TrophyPicture}`
                              }
                              alt=""
                              className="trophy-picture"
                            />
                          )}

                          <span>
                            {team.TrophyWin || 'No'}
                          </span>

                        </div>
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

    </div>
  )
}

export default App
