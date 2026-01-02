from db import get_db

db = get_db()
rows = db.execute("SELECT * FROM users").fetchall()
for r in rows:
    print(dict(r))
