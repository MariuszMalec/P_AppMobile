import { useEffect, useState } from 'react'
import API_URL from './api'

const imgUrl = p => (!p ? '' : p.startsWith('http') ? p : `${API_URL}${p}`)

export default function Trophies({ onBack }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [q, setQ] = useState('')
  const [edit, setEdit] = useState(null)
  const [editError, setEditError] = useState('')

  const load = () => {
    fetch(`${API_URL}/api/trophies`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(d => { setItems(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }

  useEffect(load, [])

  const save = () => {
    setEditError('')
    fetch(`${API_URL}/api/trophies/${edit.Id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        Name: edit.Name,
        Description: edit.Description,
        Picture: edit.Picture,
      }),
    })
      .then(async r => {
        const d = await r.json()
        if (!r.ok) throw new Error(d.detail || `HTTP ${r.status}`)
      })
      .then(() => { setEdit(null); load() })
      .catch(e => setEditError(e.message))
  }

  const shown = items.filter(t =>
    `${t.Name} ${t.Description || ''} ${t.TeamName || ''}`
      .toLowerCase()
      .includes(q.trim().toLowerCase())
  )

  return (
    <div className="tr-page">
      <div className="tr-top">
        <button className="tr-back" onClick={onBack}>← Home</button>
        <h1>🏆 Trofea</h1>
      </div>

      <input
        className="tr-search"
        placeholder="Szukaj pucharu lub drużyny"
        value={q}
        onChange={e => setQ(e.target.value)}
      />
      <p className="tr-count">{loading ? 'Ładowanie...' : `${shown.length} pucharów`}</p>
      {error && <div className="tr-msg">BŁĄD: {error}</div>}

      <div className="tr-grid">
        {shown.map(t => (
          <div className="tr-card" key={t.Id}>
            {t.Picture && <img src={imgUrl(t.Picture)} alt="" loading="lazy" decoding="async" />}
            <div className="tr-name">{t.Name}</div>
            {t.Description && <div className="tr-desc">{t.Description}</div>}
            {t.TeamName && <div className="tr-team">🛡️ {t.TeamName}</div>}
            <button className="tr-edit" onClick={() => { setEditError(''); setEdit({ ...t }) }}>
              ✏️ Edytuj
            </button>
          </div>
        ))}
      </div>

      {edit && (
        <div className="modal-backdrop" onClick={() => setEdit(null)}>
          <div className="team-modal create-team-modal" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setEdit(null)}>×</button>
            <h2>Edit Trophy</h2>
            {editError && <div className="create-team-error">⚠️ {editError}</div>}
            <div className="create-team-form">
              <label>Name *
                <input value={edit.Name || ''} onChange={e => setEdit({ ...edit, Name: e.target.value })} />
              </label>
              <label>Description
                <input value={edit.Description || ''} onChange={e => setEdit({ ...edit, Description: e.target.value })} />
              </label>
              <label>Picture (URL or filename)
                <input value={edit.Picture || ''} onChange={e => setEdit({ ...edit, Picture: e.target.value })} />
              </label>
            </div>
            <div className="create-team-footer">
              <button type="button" className="create-team-cancel" onClick={() => setEdit(null)}>Cancel</button>
              <button type="button" className="create-team-submit" onClick={save}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
