import sqlite3
c = sqlite3.connect("sws.db")

rows = [
    ("Siarka", 1998, "Gustavo Lopez", 26, 6, 36),
    ("Siarka", 1998, "Pier", 12, 3, 24),
    ("Siarka", 1998, "Leszek Jedraszczyk", 12, 5, 20),
    ("Siarka", 1998, "Krzysztof Zagorski", 16, 0, 16),
    ("Reggiana", 1998, "Bartosz Karwan", 20, 6, 33),
    ("Reggiana", 1998, "Piotr Banski", 14, 4, 28),
    ("Reggiana", 2000, "Pier", 20, 4, 32),
    ("Reggiana", 2000, "Piotr Banski", 19, 4, 27),
    ("Reggiana", 2000, "Andrzej Bialek", 15, 3, 27),
]
for team, season, player, lge, cup, tot in rows:
    c.execute(
        "INSERT OR REPLACE INTO Scorers "
        "(TeamName, Season, Player, League, Cup, Europe, Total) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (team, season, player, lge, cup, tot - lge - cup, tot),
    )

tops = [("Siarka", 1998, "Gustavo Lopez"),
        ("Reggiana", 1998, "Bartosz Karwan"),
        ("Reggiana", 2000, "Pier")]
for team, season, player in tops:
    c.execute("UPDATE Teams SET TopScorer = ? WHERE Name = ? AND Season = ?",
              (player, team, season))
c.commit()

for team, season, _ in tops:
    print(team, season)
    for r in c.execute(
        "SELECT Player, League, Cup, Europe, Total FROM Scorers "
        "WHERE TeamName = ? AND Season = ? ORDER BY Total DESC", (team, season)):
        print("   ", r)
