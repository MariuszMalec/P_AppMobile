import sqlite3
c = sqlite3.connect("sws.db")
print("Scorers:", c.execute("SELECT COUNT(*) FROM Scorers").fetchone()[0])
print("Perugia 1998 TopScorer:", c.execute(
    "SELECT DISTINCT TopScorer FROM Teams WHERE Name='Perugia' AND Season=1998").fetchall())
for r in c.execute(
    "SELECT Player, League, Cup, Europe, Total FROM Scorers "
    "WHERE TeamName='Perugia' AND Season=1998 ORDER BY Total DESC"):
    print(r)
