const TILES = [
  { page: 'clients', icon: '👥', title: 'Klienci', desc: 'Lista i dane klientów', cls: 'tile-blue' },
  { page: 'sessions', icon: '📅', title: 'Sesje', desc: 'Kalendarz tygodnia', cls: 'tile-green' },
  { page: 'stats', icon: '📊', title: 'Statystyki', desc: 'Podsumowanie pracy', cls: 'tile-purple' },
  { page: 'settings', icon: '⚙️', title: 'Ustawienia', desc: 'Kopie i import bazy', cls: 'tile-orange' },
]

export default function Home({ onNavigate }) {
  const today = new Date().toLocaleDateString('pl-PL', {
    weekday: 'long', day: 'numeric', month: 'long',
  })
  return (
    <main className="home-page">
      <header className="home-header">
        <h1>Meetings</h1>
        <p>{today}</p>
      </header>
      <div className="home-grid">
        {TILES.map((t) => (
          <button key={t.page} className={`home-tile ${t.cls}`} onClick={() => onNavigate(t.page)}>
            <span className="home-tile-icon">{t.icon}</span>
            <span className="home-tile-title">{t.title}</span>
            <span className="home-tile-desc">{t.desc}</span>
          </button>
        ))}
      </div>
    </main>
  )
}
