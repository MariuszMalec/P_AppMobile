import sqlite3, os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sws.db"


def get_db():
    db_path = os.getenv("DATABASE_PATH", "sws.db")
    conn = sqlite3.connect(
        db_path,
        timeout=5.0,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()



def init_db_if_not_exists(conn):
    cur = conn.cursor()

    # =============================
    # TEAMS
    # =============================
    cur.execute("""
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

    # DELETE DUPLICATE TEAMS
    # =============================
    cur.execute("""
    DELETE FROM Teams
    WHERE Id NOT IN (
        SELECT MIN(Id)
        FROM Teams
        GROUP BY 
            Name,
            Description,
            NationalityName,
            Season,
            TopScorer,
            Picture,
            FinalResult,
            TrophyWin,
            TrophyModelId
    );
    """)

    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS unique_team_name_season_trophy
    ON Teams (Name, Season, TrophyWin);
    """)

    # =============================
    # TROPHIES
    # =============================
    cur.execute("""
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

    print("✅ Database initialized successfully")


def insert_trophies(conn):
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO Trophies (Id, Name, Description, Picture, TeamModelId) VALUES
        (1, "ChampionsCup", "",'https://images.unsplash.com/photo-1560003991-545650ee5f07?w=600&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8N3x8Y2hhbXBpb25zJTIwbGVhZ3VlJTIwdHJvcGh5fGVufDB8fDB8fHww',0),
        (2, "UefaCup", "",'https://plus.unsplash.com/premium_photo-1713836954462-6e6cd1eecc1c?w=600&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8dWVmYSUyMHRyb3BoeXxlbnwwfHwwfHx8MA%3D%3D',0),
        (3, "ItalyCup", "",'https://media.istockphoto.com/id/160507888/photo/cup-italy.webp?a=1&b=1&s=612x612&w=0&k=20&c=DPAZTokHN0yuObx5Nnq36drI_m9zfbfugOLK5gVGC2A=',0),
        (4, "ChampionLeague", "",'https://media.istockphoto.com/id/1400851458/photo/football-cup-isolated-on-white-background.webp?a=1&b=1&s=612x612&w=0&k=20&c=g3zX2tYdVKDq7lqR6v9d69Koy53LkiEPMexqa2Y5kIg=',0),
        (5, "CwcCup", "",'https://media.istockphoto.com/id/1400851458/photo/football-cup-isolated-on-white-background.webp?a=1&b=1&s=612x612&w=0&k=20&c=g3zX2tYdVKDq7lqR6v9d69Koy53LkiEPMexqa2Y5kIg=',0),
        (6, "PolishCup", "",'https://media.istockphoto.com/id/1313420062/photo/championship-concept-star-shaped-confetti-falling-onto-a-gold-cup-sitting-over-polish-flag.webp?a=1&b=1&s=612x612&w=0&k=20&c=6AxFVImJo7b_egX6eSPEV2TqTrHTpbKYxOpYYAecEOI=',0),
        (7, "SpanishCup", "",'https://media.istockphoto.com/id/1313122279/photo/championship-concept-star-shaped-confetti-falling-onto-a-gold-cup-sitting-over-spanish-flag.webp?a=1&b=1&s=612x612&w=0&k=20&c=cWnhUezftqUvwUTHsOK8fh3tY9BN81jPaEjWzG4WHUk=',0),
        (8, "GermanCup", "",'https://media.istockphoto.com/id/1446014501/photo/germany-championship-concept-star-shaped-confetti-falling-onto-a-gold-trophy-cup-with-german.webp?a=1&b=1&s=612x612&w=0&k=20&c=uP6hIYy7uy-d4uIGDTRINKeMXRTKvJZtIfHX3Rv4_n4=',0),
        (9, "EnglandCup", "",'https://media.istockphoto.com/id/1420090069/photo/golden-cup-in-football-stadium.webp?a=1&b=1&s=612x612&w=0&k=20&c=xjBWYI1R6n6mq5vv8dCKH0OStAt_PF845yZL7ZXZDzU=',0),
        (10, "Loser", "",'https://images.unsplash.com/photo-1612436395449-279ee9a6afd0?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8bG9zZXJ8ZW58MHx8MHx8fDA%3D',0);
    """)

    conn.commit()

    print("✅ DB ensured (tables PersonFamilies exist)")


