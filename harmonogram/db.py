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
    # ORDERS
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
        StartDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        Hours INTEGER NOT NULL DEFAULT 8,
        ExistNC INTEGER NOT NULL DEFAULT 0,
        ExistCMM INTEGER NOT NULL DEFAULT 0,
        ExistMaterial INTEGER NOT NULL DEFAULT 0,
        MachineId INTEGER NOT NULL DEFAULT 1
        -- 🔥 Kolumna Color dodamy niżej jeśli brak
    );
    """)

    # =============================
    # MACHINES
    # =============================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Machines (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL DEFAULT 'hstm',
        Description TEXT NOT NULL DEFAULT '5axis',
        Picture TEXT NOT NULL DEFAULT 'test'
    );
    """)

    # =============================
    # Sprawdź kolumny i dodaj brakujące
    # =============================
    cur.execute("PRAGMA table_info(Orders)")
    columns = [col[1] for col in cur.fetchall()]

    if "MachineId" not in columns:
        cur.execute("ALTER TABLE Orders ADD COLUMN MachineId INTEGER NOT NULL DEFAULT 1")

    if "Color" not in columns:
        cur.execute("ALTER TABLE Orders ADD COLUMN Color TEXT NOT NULL DEFAULT '#f4f4f4'")

    conn.commit()
    print("✅ Database initialized successfully with Color column")



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
            StartDate,
            Hours,
            ExistNC,
            ExistCMM,
            ExistMaterial,
            MachineId,
            Color
        ) VALUES
        -- Projekty dla LINIA1
        (1, 'IMR', '000001', '0', 'Projekt_A', 'k1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 72, 0, 0, 0, 1, '#ff9999'),

        -- Projekty dla LINIA2
        (2, 'IMR', '000002', '0', 'Projekt_B', 'k1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 16, 1, 0, 0, 2, '#99ccff'),

        -- Projekty dla LINIA3
        (3, 'IMR', '000003', '0', 'Projekt_C', 'k2', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 24, 1, 1, 0, 3, '#99ff99'),

        -- Projekty dla LINIA4
        (4, 'IMR', '000004', '0', 'Projekt_D', 'k3', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 32, 0, 1, 1, 4, '#ffcc99');
    """)

    conn.commit()
    print("✅ DB seeded with initial Orders including Color")


def insert_machines(conn):
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO Machines (
            Id,
            Name,
            Description,
            Picture
        ) VALUES
        (1, 'LINIA1', '5-axis milling machine', 'hstm_01.png'),
        (2, 'LINIA2', '5-axis milling machine', 'hstm_02.png'),
        (3, 'LINIA3', 'Coordinate Measuring Machine', 'cmm_01.png'),
        (4, 'LINIA4', 'CNC Lathe', 'lathe_01.png');
    """)

    conn.commit()
    print("✅ DB ensured (table Machines exist & seeded)")
