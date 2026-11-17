def patch(path, pairs):
    s = open(path, encoding="utf-8").read()
    for old, new in pairs:
        if s.count(old) != 1:
            raise SystemExit("%s: nie znaleziono fragmentu: %s" % (path, old[:50]))
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8").write(s)
    print("OK", path)

patch("services/scorers.py", [
    ("def get_team_scorers(db, name=None, team_id=None):",
     "def get_team_scorers(db, name=None, team_id=None, season=None):"),
    ('''        rows = cur.execute(
            "SELECT Season, Player, League, Cup, Europe, Total FROM Scorers "
            "WHERE TeamName=? ORDER BY Season DESC, Total DESC", (name,)).fetchall()''',
     '''        sql = ("SELECT Season, Player, League, Cup, Europe, Total FROM Scorers "
               "WHERE TeamName=?")
        args = [name]
        if season:
            sql += " AND Season=?"
            args.append(season)
        sql += " ORDER BY Season DESC, Total DESC"
        rows = cur.execute(sql, args).fetchall()'''),
    ('return {"names": names, "name": name,',
     'return {"season": season, "names": names, "name": name,'),
])

patch("routers/team_scorers.py", [
    ("team_id: int = Query(None), db=Depends(get_db)):",
     "team_id: int = Query(None), season: int = Query(None),\n                 db=Depends(get_db)):"),
    ("get_team_scorers(db, name, team_id)",
     "get_team_scorers(db, name, team_id, season)"),
])

patch("templates/team_scorers.html", [
    ('<h2 class="h6 mb-2">{{ name }}</h2>',
     '<h2 class="h6 mb-2">{{ name }}{% if season %} - sezon {{ season }}{% endif %}</h2>\n'
     '{% if season %}<a href="/teams/scorers?name={{ name }}" class="btn btn-sm btn-outline-secondary mb-2">Wszystkie lata</a>{% endif %}'),
])

patch("templates/teams.html", [
    ('/teams/scorers?team_id={{ t.Id }}"',
     '/teams/scorers?team_id={{ t.Id }}&season={{ t.Season }}"'),
])
