import sqlite3, difflib
from PIL import Image

src = open("ocr_scorers.py", encoding="utf-8").read().split("db = sqlite3.connect")[0]
exec(src)

TEAM, SEASON = "Perugia", 1998

c = sqlite3.connect("sws.db")
pic = c.execute(
    "SELECT Picture FROM Teams WHERE Name = ? AND Season = ?", (TEAM, SEASON)
).fetchone()[0].lstrip("/")

im = Image.open(pic).convert("L")
w, h = im.size
panel = im.crop((0, h // 2, w // 2, h))
W, H = panel.size
print("plik:", pic, "| rozmiar:", (w, h), "| panel:", (W, H))

y0n, y1n = int(.20 * H), int(.87 * H)
print("okno skryptu (y w panelu):", y0n, "-", y1n)

bands = find_bands(panel, int(.05 * W), int(.62 * W), int(.02 * H), int(.95 * H))
print("pasow w szerokim oknie:", len(bands))
print()

for a, b in bands:
    inside = a >= y0n and b <= y1n
    a2, b2 = max(a - 3, 0), min(b + 3, H)
    words = read_row(panel, a2, b2, W)
    p = parse(words)
    if p:
        name, club, digits = p
        ratio = difflib.SequenceMatcher(None, norm(club), norm(TEAM)).ratio()
        info = f"name={name!r} club={club!r} digits={digits} ratio={ratio:.2f}"
    else:
        info = "parse=None"
    flag = "W OKNIE" if inside else "POZA OKNEM"
    print(f"[{flag}] y={a}-{b} words={words}")
    print("            ", info)
