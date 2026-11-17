p = "ocr_scorers.py"
s = open(p, encoding="utf-8").read()

if "def merged_bands" in s:
    raise SystemExit("Już zastosowane")

old = "find_bands(panel, int(.05*W), int(.62*W), int(.05*H), int(.87*H))"
if s.count(old) != 1:
    raise SystemExit("Nie znaleziono linii z oknem (policzono: %d)" % s.count(old))
s = s.replace(old, "merged_bands(panel, W, H)")

helper = """
def merged_bands(panel, W, H):
    main = find_bands(panel, int(.05*W), int(.62*W), int(.20*H), int(.87*H))
    top = find_bands(panel, int(.05*W), int(.62*W), int(.02*H), int(.20*H) + 20)
    out = list(main)
    for t in top:
        if all(abs(t[0] - m[0]) > 4 for m in main):
            out.append(t)
    return sorted(out)

"""
marker = "db = sqlite3.connect"
i = s.find(marker)
if i == -1:
    raise SystemExit("Nie znaleziono miejsca wstawienia")
s = s[:i] + helper + s[i:]
open(p, "w", encoding="utf-8").write(s)
print("OK")
