from pathlib import Path
import shutil
import re

path = Path("src/App.jsx")
content = path.read_text(encoding="utf-8")

pattern = re.compile(
    r"(?m)^([ \t]*)\} catch \(err\) \{\n"
    r"[ \t]*setMessage\(''\)\n"
    r"[ \t]*setError\(`Import: \$\{err\.message\}`\)\n"
    r"[ \t]*\}"
)

def replacement(match):
    indent = match.group(1)
    inner = indent + "  "

    lines = [
        "} catch (err) {",
        "setMessage('')",
        "setError(`Import: ${err.message}`)",
        "",
        "const log = [",
        "'MEETINGS - LOG BŁĘDU IMPORTU',",
        "'================================',",
        "`Data: ${new Date().toLocaleString()}`,",
        "`API: ${API_URL}`,",
        "'' ,",
        "'PLIK BAZY:',",
        "`Nazwa: ${file.name}`,",
        "`Rozmiar: ${file.size} bajtów`,",
        "`Typ: ${file.type || 'nieznany'}`,",
        "'' ,",
        "'BŁĄD:',",
        "`Nazwa błędu: ${err?.name || 'brak'}`,",
        "`Komunikat: ${err?.message || String(err)}`,",
        "'' ,",
        "'STACK:',",
        "err?.stack || 'Brak informacji',",
        "'' ,",
        "'PRZEGLĄDARKA:',",
        "navigator.userAgent,",
        "].join('\\n')",
        "",
        "const blob = new Blob([log], { type: 'text/plain;charset=utf-8' })",
        "const url = URL.createObjectURL(blob)",
        "const link = document.createElement('a')",
        "link.href = url",
        "link.download = `meetings-import-error-${Date.now()}.txt`",
        "document.body.appendChild(link)",
        "link.click()",
        "link.remove()",
        "setTimeout(() => URL.revokeObjectURL(url), 2000)",
        "}"
    ]

    return indent + ("\n" + inner).join(lines)

new_content, count = pattern.subn(replacement, content)

if count != 1:
    print(f"STOP: znaleziono {count} pasujących bloków. App.jsx bez zmian.")
    raise SystemExit(1)

shutil.copy2(path, "src/App.jsx.bak")
path.write_text(new_content, encoding="utf-8")

print("OK: dodano log błędu importu.")
print("Kopia: src/App.jsx.bak")
