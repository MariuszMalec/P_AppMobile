import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

// TEST CZASU (tymczasowy)
const t0 = performance.now()
const box = document.createElement('div')
box.style.cssText =
  'position:fixed;left:6px;bottom:6px;z-index:9999;padding:6px 10px;' +
  'background:#000c;color:#0f0;font:14px monospace;border-radius:8px;pointer-events:none'
box.textContent = 'mierzę...'
document.body.appendChild(box)
const timer = setInterval(() => {
  if (document.querySelector('.teams-table tbody tr')) {
    box.textContent = 'lista: ' + Math.round(performance.now() - t0) + ' ms'
    clearInterval(timer)
  }
}, 20)
