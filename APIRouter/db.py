import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "activity.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db_if_not_exists():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ==========================================================
    # PersonFamilies
    # ==========================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS PersonFamilies (
            Id INTEGER PRIMARY KEY,
            PersonName INTEGER NOT NULL,
            PersonPicture TEXT
        )
    """)

    # ==========================================================
    # PictureActivities
    # ==========================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS PictureActivities (
            Id INTEGER PRIMARY KEY,
            ActivityName INTEGER NOT NULL UNIQUE,
            Name TEXT NOT NULL,
            Picture TEXT
        )
    """)

    # ==========================================================
    # ActiviesDays
    # StartTime / EndTime = sekundy od 00:00
    # ==========================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ActiviesDays (
            Id INTEGER PRIMARY KEY,
            CreatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
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

    # ==========================================================
    # TRIGGER: blokada nakładających się czasów (INSERT)
    # ==========================================================

    cur.execute("DROP TRIGGER IF EXISTS trg_no_time_overlap_insert;")

    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_no_time_overlap_insert
        BEFORE INSERT ON ActiviesDays
        BEGIN
            SELECT
                RAISE(ABORT, 'TIME_OVERLAP')
            WHERE EXISTS (
                SELECT 1
                FROM ActiviesDays
                WHERE
                    DayOfWeek = NEW.DayOfWeek
                    AND ModelPersonFamilyId = NEW.ModelPersonFamilyId
                    AND time(NEW.StartTime) < time(EndTime)
                    AND time(NEW.EndTime)   > time(StartTime)
            );
        END;


    """)


    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")


def insert_person_families():
    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO PersonFamilies (Id, PersonName, PersonPicture) VALUES
        (1, 1, 'https://images.unsplash.com/photo-1516733725897-1aa73b87c8e8?auto=format&fit=crop&q=80&w=2070'),
        (2, 2, 'https://plus.unsplash.com/premium_photo-1661274027494-1d556441e1c4?q=80&w=2070&auto=format&fit=crop'),
        (3, 3, 'https://images.unsplash.com/photo-1516627145497-ae6968895b74?q=80&w=2040&auto=format&fit=crop'),
        (4, 4, 'https://images.unsplash.com/photo-1566004100631-35d015d6a491?q=80&w=2070&auto=format&fit=crop'),
        (5, 0, 'https://images.unsplash.com/photo-1696446702183-cbd13d78e1e7?q=80&w=2070&auto=format&fit=crop');
    """)

    conn.commit()
    conn.close()
    print("✅ DB ensured (tables PersonFamilies exist)")


def insert_picture_activities():
    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO PictureActivities (Id, ActivityName, Name, Picture) VALUES
        (1,  1,  'Sprzatanie_lazienki', 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?q=80&w=2070&auto=format&fit=crop'),
        (2,  2,  'Basen',              'https://images.unsplash.com/photo-1575429198097-0414ec08e8cd?auto=format&fit=crop&w=2070&q=80'),
        (3,  3,  'Pranie',             'https://plus.unsplash.com/premium_photo-1664372899448-05788a69406a?auto=format&fit=crop&w=1795'),
        (4,  4,  'Odrabianie_lekcji',   'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=2022'),
        (5,  5,  'Czas_spac',          'https://images.unsplash.com/photo-1558427400-bc691467a8a9?auto=format&fit=crop&w=1924'),
        (6,  6,  'Czas_do_pracy',      'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=2070'),
        (7,  7,  'Bajki',              'https://images.unsplash.com/photo-1515041219749-89347f83291a?auto=format&fit=crop&w=1974'),
        (8,  8,  'Wstazka',            'https://images.unsplash.com/photo-1599058917212-d750089bc07e?auto=format&fit=crop&w=2069'),
        (10, 10, 'Zamiatanie_pokoji',  'https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?auto=format&fit=crop&w=1974'),
        (11, 11, 'Sprzatanie_kuchni',  'https://images.unsplash.com/photo-1600585152220-90363fe7e115?auto=format&fit=crop&w=2070'),
        (12, 12, 'Rysowanie',          'https://plus.unsplash.com/premium_photo-1673514503010-58c013e17aae?auto=format&fit=crop&w=2070'),
        (13, 13, 'Obiad',              'https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=2072'),
        (14, 14, 'Czas_tylko_taty',    'https://images.unsplash.com/photo-1598550476439-6847785fcea6?auto=format&fit=crop&w=2070'),
        (15, 15, 'Czas_tylko_mamy',    'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=1798'),
        (16, 16, 'Spacer',             'https://images.unsplash.com/photo-1606474226448-4aa808468efc?auto=format&fit=crop&w=1990'),
        (17, 17, 'Gry_i_zabawy',       'https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?auto=format&fit=crop&w=2070'),
        (18, 18, 'Sniadanie',          'https://images.unsplash.com/photo-1615937722923-67f6deaf2cc9?auto=format&fit=crop&w=870'),
        (19, 19, 'Malowanie',          'https://images.unsplash.com/photo-1456086272160-b28b0645b729?auto=format&fit=crop&w=1632'),
        (20, 20, 'Cwiczenia_fizyczne', 'https://images.unsplash.com/photo-1591291621164-2c6367723315?auto=format&fit=crop&w=871'),
        (21, 21, 'Czas_z_mama',        'https://images.unsplash.com/photo-1623249288685-835abe0123b4?auto=format&fit=crop&w=871'),
        (22, 22, 'Czas_z_tata',        'https://images.unsplash.com/photo-1437943085269-6da5dd4295bf?auto=format&fit=crop&w=1170'),
        (23, 23, 'Tance',              'https://images.unsplash.com/photo-1504609813442-a8924e83f76e?auto=format&fit=crop&w=1170'),
        (24, 24, 'Test',               'https://images.unsplash.com/photo-1606326608690-4e0281b1e588?w=500&auto=format&fit=crop&q=60');
    """)

    conn.commit()
    conn.close()
    print("✅ DB ensured (tables PictureActivities exist)")


def insert_activities_days():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # ⬅️ DODAJ TO
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT OR IGNORE INTO ActiviesDays
            ("Id","CreatedAt","StartTime","EndTime","Description","DayOfWeek","ModelPersonFamilyId","ModelPictureActivityId")
            VALUES
            (1,"2025-12-30 14:13:52.785602","16:00:00","17:00:00","Rysowanie",1,1,12),
            (2,"2025-12-30 14:13:52.934944","19:00:00","20:30:00","Na dolinke",4,3,2),
            (3,"2025-12-30 14:13:52.943035","16:15:00","17:15:00","Do brodwaya",5,3,8),
            (4,"2025-12-30 14:13:52.947239","19:30:00","20:00:00","Wieczorynka",2,3,7),
            (5,"2025-12-30 14:13:52.951253","19:30:00","20:00:00","Wieczorynka",3,4,7),
            (6,"2025-12-30 14:13:52.95517","19:00:00","20:00:00","Bajka fabularna dla wszystkich",1,5,7),
            (7,"2025-12-30 14:13:52.959238","09:30:00","17:30:00","Kurcze, nie lubie poniedzialkow",2,1,6),
            (8,"2025-12-30 14:13:52.963023","08:00:00","16:00:00","Kurcze",3,1,6),
            (9,"2025-12-30 14:13:52.967263","09:30:00","17:30:00","Kurcze",4,1,6),
            (10,"2025-12-30 14:13:52.971466","08:00:00","16:00:00","Kurcze",5,1,6),
            (11,"2025-12-30 14:13:52.97589","09:00:00","17:00:00","Kurcze",6,1,6),
            (12,"2025-12-30 14:13:52.979659","20:00:00","22:30:00","Czas spac",2,1,5),
            (13,"2025-12-30 14:13:52.98346","20:00:00","22:30:00","Czas spac",3,2,5),
            (14,"2025-12-30 14:13:52.987156","20:00:00","22:30:00","Czas spac",4,1,5),
            (15,"2025-12-30 14:13:52.991941","20:00:00","22:30:00","Czas spac",5,2,5),
            (16,"2025-12-30 14:13:52.996575","20:00:00","22:30:00","Czas spac",6,1,5),
            (17,"2025-12-30 14:13:53.000994","20:00:00","22:30:00","Czas spac",7,2,5),
            (18,"2025-12-30 14:13:53.005471","20:00:00","22:30:00","Czas spac",1,5,5),
            (19,"2025-12-30 14:13:53.009693","18:30:00","19:00:00","Porzadki",2,1,11),
            (20,"2025-12-30 14:13:53.013561","18:30:00","19:00:00","Porzadki",5,1,11),
            (21,"2025-12-30 14:13:53.017221","18:30:00","19:00:00","Porzadki",4,2,11),
            (22,"2025-12-30 14:13:53.021144","18:30:00","19:00:00","Porzadki",5,2,1),
            (23,"2025-12-30 14:13:53.026226","18:30:00","19:00:00","Porzadki",6,1,11),
            (24,"2025-12-30 14:13:53.030973","18:30:00","19:00:00","Porzadki",7,2,11),
            (25,"2025-12-30 14:13:53.03487","18:30:00","19:00:00","Porzadki",1,1,11),
            (26,"2025-12-30 14:13:53.039259","17:30:00","18:00:00","Lekcje",2,2,4),
            (27,"2025-12-30 14:13:53.043588","17:30:00","18:00:00","Lekcje",4,2,4),
            (28,"2025-12-30 14:13:53.047437","17:30:00","18:00:00","Lekcje",5,1,4),
            (29,"2025-12-30 14:13:53.05108","17:30:00","21:00:00","Ciuszki",3,1,3),
            (30,"2025-12-30 14:13:53.055381","17:30:00","21:00:00","Ciuszki",6,2,3),
            (31,"2025-12-30 14:13:53.059554","10:30:00","12:30:00","Ciuszki",1,2,3),
            (32,"2025-12-30 14:13:53.06324","12:30:00","14:30:00","Czas na obiadek",7,2,13),
            (33,"2025-12-30 14:13:53.06717","12:30:00","14:30:00","Czas na obiadek",1,1,13),
            (34,"2025-12-30 14:13:53.072829","15:30:00","16:00:00","Kibelek",7,2,1),
            (35,"2025-12-30 14:13:53.078669","19:30:00","21:30:00","Czas na relaks",4,2,15),
            (36,"2025-12-30 14:13:53.078669","23:01:00","23:30:00","Czas na relaks",5,1,15),
            (37,"2025-12-31 14:13:53.082876","21:00:00","23:00:00","Laptopik czeka",5,1,14);
        """)

        conn.commit()
        conn.close()
        print("✅ DB ensured (tables ActiviesDays exist)")

    except sqlite3.IntegrityError as e:
        if "TIME_OVERLAP" in str(e):
            print("⚠️ Konflikt czasowy – insert przerwany przez trigger")
        else:
            raise

    finally:
        conn.close()  
