import sqlite3
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "meetings.db"


def get_db():
    db_path = os.getenv("DATABASE_PATH", "meetings.db")

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

    # =========================================
    # CLIENT
    # =========================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Client (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            CreatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FirstName TEXT,
            LastName TEXT NOT NULL,
            Age INTEGER DEFAULT 0 CHECK(Age >= 0),
            Description TEXT,
            Phone TEXT,
            Gender TEXT CHECK(Gender IN ('male', 'female', 'other')),
            IsActive INTEGER DEFAULT 1
        )
    """)

    # =========================================
    # SESSION
    # =========================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Session (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            CreatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            ClientId INTEGER NOT NULL,

            StartTime TEXT NOT NULL,
            EndTime TEXT NOT NULL,

            Description TEXT,

            DayOfWeek INTEGER NOT NULL
                CHECK(DayOfWeek BETWEEN 1 AND 7),

            SessionDate TEXT NOT NULL,

            -- =================================
            -- CYKLICZNE SESJE
            -- =================================
            -- NULL = zwykła sesja
            -- liczba = grupa sesji cyklicznych
            RecurringGroupId INTEGER DEFAULT NULL,

            IsActive INTEGER DEFAULT 1,

            FOREIGN KEY (ClientId)
                REFERENCES Client(Id)
                ON DELETE CASCADE,

            CHECK (EndTime > StartTime),

            CHECK (
                length(StartTime) = 5
                AND substr(StartTime, 3, 1) = ':'
            ),

            CHECK (
                length(EndTime) = 5
                AND substr(EndTime, 3, 1) = ':'
            )
        )
    """)

    # =========================================
    # MIGRACJA ISTNIEJĄCEJ BAZY
    # =========================================
    #
    # Jeżeli tabela Session już istniała
    # przed dodaniem RecurringGroupId,
    # CREATE TABLE IF NOT EXISTS jej nie zmieni.
    #
    # Dlatego sprawdzamy, czy kolumna istnieje.
    # =========================================

    columns = cur.execute("""
        PRAGMA table_info(Session)
    """).fetchall()

    column_names = {
        column["name"]
        for column in columns
    }

    if "RecurringGroupId" not in column_names:

        cur.execute("""
            ALTER TABLE Session
            ADD COLUMN RecurringGroupId INTEGER DEFAULT NULL
        """)

        print("✅ Dodano kolumnę Session.RecurringGroupId")

    conn.commit()

    print("✅ Database initialized successfully")


def insert_clients(conn):
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO Client
        (
            Id,
            FirstName,
            LastName,
            Age,
            Description,
            Phone,
            Gender
        )
        VALUES
        (
            1,
            "Jan",
            "Kowalski",
            30,
            "Stały klient",
            "123456789",
            "male"
        ),
        (
            2,
            "Anna",
            "Nowak",
            25,
            "Nowa klientka",
            "987654321",
            "female"
        ),
        (
            3,
            "Piotr",
            "Zielinski",
            40,
            "VIP",
            "555666777",
            "male"
        ),
        (
            4,
            "Kasia",
            "Wisniewska",
            35,
            "Lubi poranne godziny",
            "222333444",
            "female"
        ),
        (
            5,
            "Tomek",
            "Lewandowski",
            28,
            "Elastyczny grafik",
            "111222333",
            "male"
        )
    """)

    conn.commit()

    print("✅ Clients inserted")


def insert_sessions(conn):
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO Session
        (
            Id,
            ClientId,
            StartTime,
            EndTime,
            Description,
            DayOfWeek,
            SessionDate,
            RecurringGroupId
        )
        VALUES
        (
            1,
            1,
            "09:00",
            "10:00",
            "Trening poranny",
            1,
            "2026-04-06",
            NULL
        ),
        (
            2,
            2,
            "11:00",
            "12:00",
            "Sesja indywidualna",
            2,
            "2026-04-07",
            NULL
        ),
        (
            3,
            3,
            "14:30",
            "15:30",
            "Trening siłowy",
            3,
            "2026-04-08",
            NULL
        ),
        (
            4,
            1,
            "16:00",
            "17:00",
            "Cardio",
            4,
            "2026-04-09",
            NULL
        ),
        (
            5,
            4,
            "18:15",
            "19:00",
            "Stretching",
            5,
            "2026-04-10",
            NULL
        )
    """)

    conn.commit()

    print("✅ Sessions inserted")
