import sqlite3, json, os
from PIL import Image, ImageDraw

TH, SAMPLES, TOL, MIN_N, FW, FH = 170, 60, 0.06, 2, 6, 9

def find_bands(panel, x0, x1, y0, y1):
    px = panel.load()
    hits = [sum(1 for x in range(x0, x1) if px[x, y] > TH) >= 3 for y in range(y0, y1)]
    bands, start, gap = [], None, 0
    for i, h in enumerate(hits):
        if h:
            if start is None: start = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap > 1:
                bands.append((start + y0, i - gap + y0 + 1)); start = None
    if start is not None: bands.append((start + y0, y1))
    return [b for b in bands if 7 <= b[1] - b[0] <= 40]

def segments(panel, a, b, x0, x1):
    px = panel.load()
    cols = [any(px[x, y] > TH for y in range(a, b)) for x in range(x0, x1)]
    segs, s = [], None
    for i, c in enumerate(cols):
        if c and s is None: s = i
        if not c and s is not None:
            segs.append((s + x0, i + x0)); s = None
    if s is not None: segs.append((s + x0, x1))
    return segs

def tight(panel, x, x2, a, b):
    bw = panel.crop((x, a, x2, b)).point(lambda p: 255 if p > TH else 0)
    box = bw.getbbox()
    if not box: return None
    top, bot = box[1], box[3]
    g = bw.crop(box).resize((FW, FH), Image.BILINEAR)
    f = [p / 255 for p in g.getdata()]
    return f, (box[2] - box[0]), (bot - top), top, bw.crop(box)

def dist(f1, f2):
    return sum(abs(p - q) for p, q in zip(f1, f2)) / len(f1)

if __name__ == "__main__":
    db = sqlite3.connect("sws.db")
    rows = db.execute("SELECT DISTINCT Picture FROM Teams").fetchall()
    paths = [r[0].lstrip("/") for r in rows if r[0] and os.path.exists(r[0].lstrip("/"))]
    paths = paths[::max(1, len(paths) // SAMPLES)][:SAMPLES]
    clusters = []
    for path in paths:
        im = Image.open(path).convert("L")
        w, h = im.size
        panel = im.crop((0, h // 2, w // 2, h)); W, H = panel.size
        for (a, b) in find_bands(panel, int(.05*W), int(.62*W), int(.20*H), int(.87*H)):
            a, b = max(a-3, 0), min(b+3, H)
            for (x, x2) in segments(panel, a, b, int(.02*W), int(.98*W)):
                t = tight(panel, x, x2, a, b)
                if not t: continue
                f, gw, gh, top, img = t
                if gh < 6 or gw > 2.2 * gh: continue
                for c in clusters:
                    if abs(c["h"] - gh) <= 2 and abs(c["w"] - gw) <= max(1, .3*gw) and dist(c["f"], f) < TOL:
                        c["n"] += 1; break
                else:
                    clusters.append({"f": f, "w": gw, "h": gh, "n": 1, "img": img})
        print(path, "-> klastrów:", len(clusters), flush=True)

    clusters = [c for c in clusters if c["n"] >= MIN_N]
    clusters.sort(key=lambda c: -c["n"])
    clusters = clusters[:90]
    COLS, CW, CH = 10, 70, 100
    sheet = Image.new("RGB", (COLS*CW, ((len(clusters)+COLS-1)//COLS)*CH), (20, 20, 40))
    d = ImageDraw.Draw(sheet)
    for i, c in enumerate(clusters):
        g = c["img"].resize((c["img"].width*6, c["img"].height*6), Image.NEAREST).convert("RGB")
        g.thumbnail((CW-6, CH-30))
        cx, cy = (i % COLS)*CW, (i // COLS)*CH
        sheet.paste(g, (cx+3, cy+3))
        d.text((cx+3, cy+CH-22), f"#{i} x{c['n']}", fill=(255, 255, 0))
    sheet.save("glyphs.png")
    json.dump([{"f": c["f"], "w": c["w"], "h": c["h"], "n": c["n"]} for c in clusters], open("glyphs.json", "w"))
    print("Zapisano glyphs.png, znaków:", len(clusters))
