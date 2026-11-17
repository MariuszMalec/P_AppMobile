import sqlite3, shutil, subprocess, sys

shutil.copy("sws.db", "sws_before_rebuild.db")

c = sqlite3.connect("sws.db")
c.execute("""CREATE TABLE IF NOT EXISTS Scorers (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    TeamName TEXT NOT NULL, Season INTEGER NOT NULL, Player TEXT NOT NULL,
    League INTEGER DEFAULT 0, Cup INTEGER DEFAULT 0,
    Europe INTEGER DEFAULT 0, Total INTEGER DEFAULT 0,
    UNIQUE (TeamName, Season, Player))""")
c.execute("DELETE FROM Scorers")
c.commit()
c.close()

subprocess.run([sys.executable, "ocr_scorers.py", "--apply"], check=True)

# reczne poprawki z obrazkow (OCR ich nie czyta)
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
tops = [("Siarka", 1998, "Gustavo Lopez"),
        ("Reggiana", 1998, "Bartosz Karwan"),
        ("Reggiana", 2000, "Pier")]

c = sqlite3.connect("sws.db")
for team, season, player, lge, cup, tot in rows:
    c.execute("INSERT OR REPLACE INTO Scorers "
              "(TeamName, Season, Player, League, Cup, Europe, Total) "
              "VALUES (?,?,?,?,?,?,?)",
              (team, season, player, lge, cup, tot - lge - cup, tot))
for team, season, player in tops:
    c.execute("UPDATE Teams SET TopScorer=? WHERE Name=? AND Season=?",
              (player, team, season))
c.commit()

print("Scorers:", c.execute("SELECT COUNT(*) FROM Scorers").fetchone()[0])
print("Perugia 1998:", c.execute(
    "SELECT DISTINCT TopScorer FROM Teams WHERE Name='Perugia' AND Season=1998").fetchall())
