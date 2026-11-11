const API_URL =
  window.location.hostname === '127.0.0.1' &&
  window.location.port === '8000'
    ? 'http://127.0.0.1:8000'
    : 'http://127.0.0.1:8001'

export default API_URL
