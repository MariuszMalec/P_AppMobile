import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "shiftplane.db"


# =============================
# DB CONNECTION
# =============================
def get_db():
    db_path = os.getenv("DATABASE_PATH", str(DB_PATH))

    conn = sqlite3.connect(
        db_path,
        timeout=5.0,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")  # WAŻNE dla SQLite

    try:
        yield conn
    finally:
        conn.close()


# =============================
# INIT DATABASE
# =============================
def init_db_if_not_exists(conn):
    cur = conn.cursor()

    # =============================
    # Employees
    # =============================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Employees (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        FirstName TEXT NOT NULL DEFAULT 'Gal',
        LastName TEXT NOT NULL DEFAULT 'Anonim',
        Picture TEXT NOT NULL DEFAULT 'http://127.0.0.1:8001/static/images/avatar1.png',
        SSO INTEGER NOT NULL DEFAULT 0,
        Color TEXT NOT NULL DEFAULT '#f4f4f4',
        Created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # =============================
    # WorkShifts
    # =============================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS WorkShifts (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL UNIQUE,
        Description TEXT NOT NULL,
        Picture TEXT NOT NULL
    );
    """)

    # =============================
    # EmployeeShifts (grafik)
    # =============================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS EmployeeShifts (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        EmployeeId INTEGER NOT NULL,
        WorkShiftId INTEGER NOT NULL,
        ShiftDate TEXT NOT NULL,
        Created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (EmployeeId) REFERENCES Employees(Id) ON DELETE CASCADE,
        FOREIGN KEY (WorkShiftId) REFERENCES WorkShifts(Id) ON DELETE CASCADE,

        UNIQUE(EmployeeId, ShiftDate)
    );
    """)

    conn.commit()
    print("✅ Database initialized successfully")


# =============================
# SEED EMPLOYEES
# =============================
def insert_employees(conn):
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO Employees (
            Id,
            FirstName,
            LastName,
            Picture,
            SSO,
            Color
        ) VALUES
        (1, 'mariusz', 'malec', 'http://127.0.0.1:8001/static/images/avatar1.png', 999999999, '#ff9999'),
        (2, 'bobek', 'bobkowy', 'http://127.0.0.1:8001/static/images/avatar2.png', 999999999, '#99ccff'),
        (3, 'pracus', 'prackowy', 'http://127.0.0.1:8001/static/images/avatar3.png', 999999999, '#99ff99');
    """)

    conn.commit()
    print("✅ Employees seeded")


# =============================
# SEED WORKSHIFTS
# =============================
def insert_workshifts(conn):
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO WorkShifts (
            Id,
            Name,
            Description,
            Picture
        ) VALUES
        (1, '1zmiana', '8:00 - 15:00', '1zmiana.png'),
        (2, '2zmiana', '15:00 - 22:00', '2zmiana.png'),
        (3, '3zmiana', '22:00 - 08:00', '3zmiana.png'),
        (4, 'dayoff', 'Dzień wolny', 'dayoff.png');
    """)

    conn.commit()
    print("✅ WorkShifts seeded")


# =============================
# SEED EMPLOYEE SHIFTS (grafik)
# =============================
def insert_employee_shifts(conn):
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO EmployeeShifts (
            EmployeeId,
            WorkShiftId,
            ShiftDate
        ) VALUES
        (1, 1, '2026-02-01'),
        (1, 2, '2026-02-02'),
        (1, 3, '2026-02-03'),

        (2, 2, '2026-02-01'),
        (2, 3, '2026-02-02'),
        (2, 4, '2026-02-03'),

        (3, 1, '2026-02-01'),
        (3, 4, '2026-02-02'),
        (3, 2, '2026-02-03');
    """)

    conn.commit()
    print("✅ EmployeeShifts seeded")
