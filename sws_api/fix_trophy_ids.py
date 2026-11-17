import sqlite3, sys
APPLY = "--apply" in sys.argv
c = sqlite3.connect("sws.db"); c.row_factory = sqlite3.Row
ids = {r["Name"]: r["Id"] for r in c.execute("SELECT Id, Name FROM Trophies")}
loser = ids.get("Loser")
fix = []
for r in c.execute("SELECT Id, Name, Season, TrophyWin, TrophyModelId FROM Teams WHERE TrophyModelId = ?", (loser,)):
    tw = r["TrophyWin"]
    if tw in ids and tw != "Loser":
        fix.append((r["Id"], r["Name"], r["Season"], tw, ids[tw]))
print("do poprawy:", len(fix))
for f in fix:
    print("  ", f[1], f[2], f[3], "10 ->", f[4])
other = c.execute("SELECT Name, Season, TrophyWin FROM Teams WHERE TrophyModelId = ? AND TrophyWin NOT IN (SELECT Name FROM Trophies)", (loser,)).fetchall()
print("id=10 bez pasujacej nazwy (nie ruszam):", [tuple(o) for o in other])
if APPLY:
    for i, _, _, _, new in fix:
        c.execute("UPDATE Teams SET TrophyModelId = ? WHERE Id = ?", (new, i))
    c.commit(); print("zapisano")
else:
    print("tylko podglad (dodaj --apply)")
