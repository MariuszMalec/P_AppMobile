import { useEffect, useState } from 'react'

export default function ScrollButtons() {
  const [pos, setPos] = useState({ top: true, bottom: false })

  useEffect(() => {
    const update = () => {
      const y = window.scrollY
      const max = document.documentElement.scrollHeight - window.innerHeight
      setPos({ top: y < 150, bottom: y >= max - 150 })
    }
    update()
    window.addEventListener('scroll', update, { passive: true })
    window.addEventListener('resize', update)
    return () => {
      window.removeEventListener('scroll', update)
      window.removeEventListener('resize', update)
    }
  }, [])

  const goTop = () => window.scrollTo({ top: 0, behavior: 'smooth' })
  const goBottom = () =>
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth',
    })

  return (
    <div className="scroll-btns">
      <button
        className={pos.top ? 'hidden' : ''}
        onClick={goTop}
        aria-label="Do góry"
      >
        ↑
      </button>
      <button
        className={pos.bottom ? 'hidden' : ''}
        onClick={goBottom}
        aria-label="Na dół"
      >
        ↓
      </button>
    </div>
  )
}
