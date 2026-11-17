import sqlite3, csv
c = sqlite3.connect("sws_backup_pre_fix.db")
old = {(r[0], r[1], r[2]): r[3:] for r in c.execute(
    "SELECT TeamName,Season,Player,League,Cup,Europe,Total FROM Scorers")}
new = {}
for r in csv.DictReader(open("scorers_review.csv", encoding="utf-8")):
    if r["Player"] != "NoTopScorer":
        new[(r["Team"], int(r["Season"]), r["Player"])] = (
            int(r["LGE"]), int(r["CUP"]), int(r["EUR"]), int(r["TOT"]))
print("w bazie:", len(old), "| w CSV:", len(new))
print("tylko w bazie:", len(set(old) - set(new)))
print("tylko w CSV:", len(set(new) - set(old)))
diff = [k for k in set(old) & set(new) if old[k] != new[k]]
print("rozne liczby:", len(diff))
for k in sorted(set(old) - set(new))[:25]:
    print("BAZA   ", k, old[k])
for k in sorted(diff)[:15]:
    print("ROZNICA", k, old[k], "->", new[k])
