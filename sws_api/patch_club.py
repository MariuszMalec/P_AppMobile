p = "ocr_scorers.py"
s = open(p, encoding="utf-8").read()
old = 'if difflib.SequenceMatcher(None, norm(club), norm(t["Name"])).ratio() < 0.7:'
new = ('if not (norm(club).startswith(norm(t["Name"])) or '
       'difflib.SequenceMatcher(None, norm(club), norm(t["Name"])).ratio() >= 0.7):')
if s.count(old) != 1:
    raise SystemExit("Nie znaleziono fragmentu: %d" % s.count(old))
open(p, "w", encoding="utf-8").write(s.replace(old, new))
print("OK")
