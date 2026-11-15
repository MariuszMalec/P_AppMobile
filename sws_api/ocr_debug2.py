import sqlite3, json, sys
from PIL import Image
from glyphs_build import find_bands, segments, tight, dist

team, season = (sys.argv[1], int(sys.argv[2])) if len(sys.argv) > 2 else ("Cremonese", 1996)
GL = json.load(open("glyphs.json"))
db = sqlite3.connect("sws.db")
pic = db.execute("SELECT Picture FROM Teams WHERE Name=? AND Season=?", (team, season)).fetchone()[0].lstrip("/")
im = Image.open(pic).convert("L"); w, h = im.size
print("plik:", pic, "rozmiar:", im.size)
panel = im.crop((0, h//2, w//2, h)); W, H = panel.size
bands = find_bands(panel, int(.05*W), int(.62*W), int(.20*H), int(.87*H))
print("pasów:", len(bands))
a, b = bands[0]; a, b = max(a-3, 0), min(b+3, H)
n = 0
for (x, x2) in segments(panel, a, b, int(.02*W), int(.98*W))[-10:]:
    t = tight(panel, x, x2, a, b)
    if not t: continue
    f, gw, gh, top, img = t
    ds = sorted((dist(c["f"], f), i, c["h"]) for i, c in enumerate(GL))[:2]
    print(f"x={x}-{x2} w={gw} h={gh} najbliższe: {[(round(d,3), i, ch) for d, i, ch in ds]}")
    img.resize((img.width*10, img.height*10), Image.NEAREST).save(f"dbg_{n}.png"); n += 1
panel.crop((0, a, W, b)).resize((W*2, (b-a)*2), Image.NEAREST).save("dbg_row.png")
