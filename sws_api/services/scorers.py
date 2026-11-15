def get_team_scorers(db, name=None, team_id=None):
    cur = db.cursor()
    names = [r[0] for r in cur.execute(
        "SELECT DISTINCT TeamName FROM Scorers ORDER BY TeamName").fetchall()]
    if team_id and not name:
        row = cur.execute("SELECT Name FROM Teams WHERE Id=?", (team_id,)).fetchone()
        name = row["Name"] if row else None
    rows, career = [], []
    if name:
        rows = cur.execute(
            "SELECT Season, Player, League, Cup, Europe, Total FROM Scorers "
            "WHERE TeamName=? ORDER BY Season DESC, Total DESC", (name,)).fetchall()
        career = cur.execute(
            "SELECT Player, SUM(Total) T, SUM(League) L, SUM(Cup) C, SUM(Europe) E "
            "FROM Scorers WHERE TeamName=? GROUP BY Player ORDER BY T DESC LIMIT 10",
            (name,)).fetchall()
    best = {}
    for r in rows:
        best.setdefault(r["Season"], r["Player"])
    return {"names": names, "name": name, "rows": rows, "career": career, "best": best}
