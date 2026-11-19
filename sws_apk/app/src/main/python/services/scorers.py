def get_team_scorers(db, name=None, team_id=None, season=None):
    cur = db.cursor()
    names = [r[0] for r in cur.execute(
        "SELECT DISTINCT TeamName FROM Scorers ORDER BY TeamName").fetchall()]
    if team_id and not name:
        row = cur.execute("SELECT Name FROM Teams WHERE Id=?", (team_id,)).fetchone()
        name = row["Name"] if row else None
    rows, career = [], []
    if name:
        sql = ("SELECT Season, Player, League, Cup, Europe, Total FROM Scorers "
               "WHERE TeamName=?")
        args = [name]
        if season:
            sql += " AND Season=?"
            args.append(season)
        sql += " ORDER BY Season DESC, Total DESC"
        rows = cur.execute(sql, args).fetchall()
        career = cur.execute(
            "SELECT Player, SUM(Total) T, SUM(League) L, SUM(Cup) C, SUM(Europe) E "
            "FROM Scorers WHERE TeamName=? GROUP BY Player ORDER BY T DESC LIMIT 10",
            (name,)).fetchall()
    best = {}
    for r in rows:
        best.setdefault(r["Season"], r["Player"])
    return {"season": season, "names": names, "name": name, "rows": rows, "career": career, "best": best}
