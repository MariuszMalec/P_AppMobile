import sqlite3, os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "harmonogram.db"


def get_db():
    db_path = os.getenv("DATABASE_PATH", "harmonogram.db")
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
    # ORDER
    # =============================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Orders (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL DEFAULT 'IMR',
        Zlecenie TEXT NOT NULL DEFAULT '000000',
        Haslo TEXT NOT NULL DEFAULT '0',
        ProjectName TEXT NOT NULL DEFAULT 'test',
        TypeOfBlade TEXT NOT NULL DEFAULT 'k1',
        Exw TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        Hours INTEGER NOT NULL DEFAULT 8,
        ExistNC INTEGER NOT NULL DEFAULT 0,
        ExistCMM INTEGER NOT NULL DEFAULT 0,
        ExistMaterial INTEGER NOT NULL DEFAULT 0
    );
    """)

    # =============================
    # MACHINE
    # =============================
    # cur.execute("""
    # CREATE TABLE IF NOT EXISTS Trophies (
    #     Id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     Name TEXT NOT NULL,
    #     Description TEXT NOT NULL,
    #     Picture TEXT NOT NULL,
    #     TeamModelId INTEGER,
    #     FOREIGN KEY (TeamModelId) REFERENCES Teams(Id)
    # );
    # """)

    conn.commit()

    print("✅ Database initialized successfully")


def insert_orders(conn):
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO Orders (
            Id,
            Name,
            Zlecenie,
            Haslo,
            ProjectName,
            TypeOfBlade,
            Exw,
            Hours,
            ExistNC,
            ExistCMM,
            ExistMaterial
        ) VALUES
        (1, 'IMR', '000001', '0', 'test', 'k1', CURRENT_TIMESTAMP, 8, 0, 0, 0),
        (2, 'IMR', '000002', '0', 'test', 'k1', CURRENT_TIMESTAMP, 16, 1, 0, 0),
        (3, 'IMR', '000003', '0', 'test', 'k2', CURRENT_TIMESTAMP, 24, 1, 1, 0),
        (4, 'IMR', '000004', '0', 'project_x', 'k3', CURRENT_TIMESTAMP, 32, 0, 1, 1);
    """)

    conn.commit()

    print("✅ DB ensured (table Orders exist & seeded)")



