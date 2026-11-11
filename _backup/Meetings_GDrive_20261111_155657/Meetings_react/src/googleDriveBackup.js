import API_URL from './api'

const CLIENT_ID =
  '629429297967-9kaqj4144ruvc1ltteii8dumjndlumht.apps.googleusercontent.com'

const DRIVE_SCOPE =
  'https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/userinfo.email'

const FILE_MARKER = 'meetings-react-backup-v1'
const FILE_NAME = 'Meetings-backup.db'
const MIME_TYPE = 'application/vnd.sqlite3'

let tokenClient = null
let scriptPromise = null

function loadGoogleScript() {
  if (window.google?.accounts?.oauth2) {
    return Promise.resolve()
  }

  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = 'https://accounts.google.com/gsi/client'
      script.async = true
      script.defer = true

      script.onload = resolve
      script.onerror = () => {
        scriptPromise = null
        reject(new Error('Nie udało się załadować logowania Google.'))
      }

      document.head.appendChild(script)
    })
  }

  return scriptPromise
}

async function requestGoogleToken(prompt = '') {
  await loadGoogleScript()

  return new Promise((resolve, reject) => {
    tokenClient = window.google.accounts.oauth2.initTokenClient({
      client_id: CLIENT_ID,
      scope: DRIVE_SCOPE,
      callback: (response) => {
        if (response.error) {
          reject(new Error(response.error_description || response.error))
          return
        }

        if (!response.access_token) {
          reject(new Error('Google nie zwrócił tokenu dostępu.'))
          return
        }

        resolve(response.access_token)
      },
      error_callback: (error) => {
        reject(new Error(error?.message || 'Logowanie Google nie powiodło się.'))
      },
    })

    tokenClient.requestAccessToken({ prompt })
  })
}

async function googleRequest(url, token, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  })

  if (!response.ok) {
    const result = await response.json().catch(() => ({}))
    throw new Error(
      result.error?.message || `Google Drive: HTTP ${response.status}`
    )
  }

  if (response.status === 204) return null
  return response.json()
}

export async function connectGoogleAccount() {
  const token = await requestGoogleToken('select_account')

  const response = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!response.ok) {
    throw new Error('Nie udało się odczytać konta Google.')
  }

  const user = await response.json()

  if (!user.email) {
    throw new Error('Google nie zwrócił adresu e-mail.')
  }

  return user.email
}

export async function uploadAndShareBackup(recipientEmail, onStatus) {
  if (!recipientEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(recipientEmail)) {
    throw new Error('Podaj prawidłowy adres e-mail odbiorcy.')
  }

  onStatus?.('Łączę z Google...')
  const token = await requestGoogleToken('')

  onStatus?.('Pobieram aktualną bazę...')
  const backupResponse = await fetch(
    `${API_URL}/api/backup/export`
  )

  if (!backupResponse.ok) {
    throw new Error(`Nie udało się pobrać bazy: HTTP ${backupResponse.status}`)
  }

  const databaseBlob = await backupResponse.blob()

  if (!databaseBlob.size) {
    throw new Error('Pobrana baza jest pusta.')
  }

  onStatus?.('Szukam poprzedniej kopii na Dysku...')
  const query = `trashed = false and appProperties has { key='meetingsBackup' and value='${FILE_MARKER}' }`
  const searchUrl =
    'https://www.googleapis.com/drive/v3/files?q=' +
    encodeURIComponent(query) +
    '&fields=files(id,name,webViewLink)'

  const searchResult = await googleRequest(searchUrl, token)
  const existingFile = searchResult.files?.[0]

  let file

  if (existingFile) {
    onStatus?.('Aktualizuję istniejącą kopię...')
    file = await googleRequest(
      `https://www.googleapis.com/upload/drive/v3/files/${existingFile.id}?uploadType=media&fields=id,name,webViewLink`,
      token,
      {
        method: 'PATCH',
        headers: { 'Content-Type': MIME_TYPE },
        body: databaseBlob,
      }
    )
  } else {
    onStatus?.('Tworzę kopię na Dysku...')
    const metadata = {
      name: FILE_NAME,
      mimeType: MIME_TYPE,
      appProperties: { meetingsBackup: FILE_MARKER },
    }

    const form = new FormData()
    form.append(
      'metadata',
      new Blob([JSON.stringify(metadata)], { type: 'application/json' })
    )
    form.append('file', databaseBlob, FILE_NAME)

    file = await googleRequest(
      'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink',
      token,
      { method: 'POST', body: form }
    )
  }

  onStatus?.('Sprawdzam dostęp odbiorcy...')
  const permissionsUrl =
    `https://www.googleapis.com/drive/v3/files/${file.id}/permissions` +
    '?fields=permissions(id,type,role,emailAddress)'

  const permissionsResult = await googleRequest(permissionsUrl, token)
  const existingPermission = permissionsResult.permissions?.find(
    (permission) =>
      permission.type === 'user' &&
      permission.emailAddress?.toLowerCase() === recipientEmail.toLowerCase()
  )

  if (!existingPermission) {
    onStatus?.('Udostępniam kopię odbiorcy...')
    await googleRequest(
      `https://www.googleapis.com/drive/v3/files/${file.id}/permissions?sendNotificationEmail=true`,
      token,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'user',
          role: 'reader',
          emailAddress: recipientEmail,
        }),
      }
    )
  }

  return {
    name: file.name || FILE_NAME,
    link: file.webViewLink || '',
    updated: Boolean(existingFile),
  }
}

