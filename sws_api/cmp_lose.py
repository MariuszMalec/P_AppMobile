import sqlite3
from services.results import get_result_status
c = sqlite3.connect("sws.db"); c.row_factory = sqlite3.Row
for team in ("ACMilan", "Reggiana"):
    print("=====", team)
    for r in c.execute("SELECT Season, FinalResult, TrophyWin, TrophyModelId FROM Teams WHERE Name=? ORDER BY Season", (team,)):
        st = get_result_status(r["FinalResult"], team)
        print(r["Season"], "|", r["FinalResult"], "|", r["TrophyWin"], "|", r["TrophyModelId"], "| lose =", st["lose"])
