import sqlite3

DB_NAME = "swsdb.sqlite"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # =============================
    # TEAMS
    # =============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Teams (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Description TEXT,
        NationalityName TEXT NOT NULL,
        Season INTEGER NOT NULL,
        TopScorer TEXT NOT NULL,
        Picture TEXT NOT NULL,
        FinalResult TEXT NOT NULL,
        TrophyWin TEXT,
        TrophyModelId INTEGER
    );
    """)

    # =============================
    # TROPHIES
    # =============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Trophies (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Description TEXT NOT NULL,
        Picture TEXT NOT NULL,
        TeamModelId INTEGER,
        FOREIGN KEY (TeamModelId) REFERENCES Teams(Id)
    );
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

if __name__ == "__main__":
    init_db()
