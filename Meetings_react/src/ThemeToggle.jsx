import { useEffect, useState } from 'react'

export default function ThemeToggle() {
  const [dark, setDark] = useState(() => {
    try {
      return localStorage.getItem('react-theme') === 'dark'
    } catch {
      return false
    }
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark-mode', dark)
    try {
      localStorage.setItem('react-theme', dark ? 'dark' : 'light')
    } catch {
      /* ignoruj */
    }
  }, [dark])

  return (
    <button
      className="theme-toggle-btn"
      onClick={() => setDark(!dark)}
      aria-label="Zmień motyw"
    >
      {dark ? '☀️' : '🌙'}
    </button>
  )
}
