import sqlite3
from datetime import datetime

DB_PATH = "activity.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ==========================================================
    # DROP TABLES (kolejność ma znaczenie – FK)
    # ==========================================================
    cur.execute("DROP TABLE IF EXISTS ActiviesDays")
    cur.execute("DROP TABLE IF EXISTS PersonFamilies")
    cur.execute("DROP TABLE IF EXISTS PictureActivities")

    # ==========================================================
    # PersonFamilies
    # ==========================================================
    cur.execute("""
        CREATE TABLE PersonFamilies (
            Id INTEGER PRIMARY KEY,
            PersonName INTEGER NOT NULL,
            PersonPicture TEXT
        )
    """)

    # ==========================================================
    # PictureActivities
    # ==========================================================
    cur.execute("""
        CREATE TABLE PictureActivities (
            Id INTEGER PRIMARY KEY,
            ActivityName INTEGER NOT NULL,
            Picture TEXT
        )
    """)

    # ==========================================================
    # ActiviesDays
    # StartTime / EndTime = sekundy od 00:00
    # ==========================================================
    cur.execute("""
        CREATE TABLE ActiviesDays (
            Id INTEGER PRIMARY KEY,
            CreatedAt TEXT NOT NULL,
            StartTime INTEGER NOT NULL,
            EndTime INTEGER NOT NULL,
            Description TEXT,
            DayOfWeek INTEGER NOT NULL,

            ModelPersonFamilyId INTEGER,
            ModelPictureActivityId INTEGER,

            FOREIGN KEY (ModelPersonFamilyId)
                REFERENCES PersonFamilies(Id)
                ON DELETE SET NULL,

            FOREIGN KEY (ModelPictureActivityId)
                REFERENCES PictureActivities(Id)
                ON DELETE SET NULL
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")


if __name__ == "__main__":
    init_db()
