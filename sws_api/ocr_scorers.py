import sqlite3, re, sys, csv, os, time, json, difflib
from PIL import Image
from glyphs_build import find_bands, segments, tight, dist, TH

APPLY = "--apply" in sys.argv
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None

MAP = {0:'I',1:'A',2:'O',3:'E',4:'R',5:'N',6:'L',7:'S',8:'2',9:'(',10:')',11:'C',12:'T',
       13:'M',14:'U',15:'K',16:'G',17:'D',18:'4',19:'Z',20:'3',21:'B',22:'5',23:'P',
       24:'W',25:'V',26:'H',27:'6',28:'7',29:'F',30:'8',31:'9',32:'J',33:'Y',36:'X'}
TO_DIGIT = {'I':'1','O':'0','D':'0','S':'5','Z':'2','B':'8','G':'6'}
TO_LETTER = {'1':'I','0':'O','2':'Z','5':'S','8':'B','6':'G'}
GL = json.load(open("glyphs.json"))
norm = lambda x: re.sub(r"[^a-z]", "", x.lower())

def classify(f, gw, gh):
    best, bd = None, 9
    for i, ch in MAP.items():
        if i >= len(GL): continue
        c = GL[i]
        if abs(c["h"] - gh) > 2: continue
        d = dist(c["f"], f)
        if d < bd: best, bd = ch, d
    return best if bd < 0.20 else "?"

def read_row(panel, a, b, W):
    segs = segments(panel, a, b, int(.02*W), int(.98*W))
    glyphs = []
    for (x, x2) in segs:
        t = tight(panel, x, x2, a, b)
        if not t: continue
        f, gw, gh, top, img = t
        if gh < 6: continue
        glyphs.append((x, x2, classify(f, gw, gh)))
    gaps = sorted(glyphs[i+1][0] - glyphs[i][1] for i in range(len(glyphs) - 1))
    med = gaps[len(gaps) // 2] if gaps else 1
    thr = max(med * 2.0, med + 2)
    words, cur = [], []
    for g in glyphs:
        if cur and g[0] - cur[-1][1] > thr:
            words.append(cur); cur = []
        cur.append(g)
    if cur: words.append(cur)
    return ["".join(g[2] for g in w) for w in words]

def parse(words):
    if len(words) < 6: return None
    nums, rest = words[-3:], words[1:-3]
    try:
        k = next(i for i, w in enumerate(rest) if w.startswith("("))
    except StopIteration:
        return None
    name = " ".join("".join(TO_LETTER.get(c, c) for c in w) for w in rest[:k]).title()
    club = "".join(rest[k:]).strip("()")
    club = "".join(TO_LETTER.get(c, c) for c in club)
    digits = ["".join(TO_DIGIT.get(c, c) for c in w) for w in nums]
    return name, club, digits

db = sqlite3.connect("sws.db"); db.row_factory = sqlite3.Row
pairs = db.execute("SELECT Name, Season, MIN(Picture) Pic FROM Teams GROUP BY Name, Season").fetchall()
if LIMIT: pairs = pairs[:LIMIT]
N = len(pairs); print(f"Obrazków do przetworzenia: {N}", flush=True)

ok_rows, check_rows, t0 = [], [], time.time()
try:
    for i, t in enumerate(pairs, 1):
        s0 = time.time(); path = (t["Pic"] or "").lstrip("/"); good, note = [], ""
        if not os.path.exists(path):
            note = "brak pliku"
        else:
            try:
                im = Image.open(path).convert("L"); w, h = im.size
                panel = im.crop((0, h // 2, w // 2, h)); W, H = panel.size
                for (a, b) in find_bands(panel, int(.05*W), int(.62*W), int(.20*H), int(.87*H)):
                    a, b = max(a-3, 0), min(b+3, H)
                    p = parse(read_row(panel, a, b, W))
                    if not p: continue
                    name, club, digits = p
                    if difflib.SequenceMatcher(None, norm(club), norm(t["Name"])).ratio() < 0.7:
                        continue
                    if "?" in name or any(not d.isdigit() for d in digits):
                        check_rows.append((t["Name"], t["Season"], name, *digits)); continue
                    lge, cup, tot = map(int, digits)
                    if tot < lge + cup:
                        check_rows.append((t["Name"], t["Season"], name, *digits)); continue
                    good.append((name, lge, cup, tot - lge - cup, tot))
            except Exception as e:
                note = f"błąd: {e}"
        for r in good: ok_rows.append((t["Name"], t["Season"], *r))
        if not good: ok_rows.append((t["Name"], t["Season"], "NoTopScorer", 0, 0, 0, 0))
        if APPLY:
            for r in good:
                db.execute("INSERT OR REPLACE INTO Scorers (TeamName,Season,Player,League,Cup,Europe,Total) VALUES (?,?,?,?,?,?,?)",
                           (t["Name"], t["Season"], *r))
            best = max(good, key=lambda r: r[4])[0] if good else "NoTopScorer"
            db.execute("UPDATE Teams SET TopScorer=? WHERE Name=? AND Season=?", (best, t["Name"], t["Season"]))
            db.commit()
        el = time.time() - t0
        print(f"{i}/{N} {t['Name']} {t['Season']} -> {len(good)} OK {note} ({time.time()-s0:.1f}s, zostało ~{el/i*(N-i)/60:.1f} min)", flush=True)
except KeyboardInterrupt:
    print("\nPrzerwano, zapisuję CSV...", flush=True)

with open("scorers_review.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows([("Team","Season","Player","LGE","CUP","EUR","TOT"), *ok_rows])
with open("scorers_check.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows([("Team","Season","Player","LGE","CUP","TOT"), *check_rows])
print("OK:", len(ok_rows), "| do sprawdzenia:", len(check_rows), "| zapisano do bazy" if APPLY else "| tylko podgląd")
