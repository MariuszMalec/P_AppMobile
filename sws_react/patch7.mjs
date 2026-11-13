import fs from 'fs'
const file = 'src/App.jsx'
let s = fs.readFileSync(file, 'utf8')
const code = fs.readFileSync('/tmp/newload.txt', 'utf8').replace(/\n$/, '\n')

if (!s.includes('abortRef')) {
  s = s.replace("import { useEffect, useState } from 'react'",
                "import { useEffect, useRef, useState } from 'react'")
  s = s.replace(
    /const loadTeams = \(\) => \{[\s\S]*?\n  \}, \[filterName, filterTrophy, filterResult, sort\]\)\n/,
    () => code
  )
}
fs.writeFileSync(file, s)
console.log('OK')
