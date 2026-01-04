from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta
from typing import Optional, List
import sqlite3
import enum

# ===============================================================
# APP
# ===============================================================

app = FastAPI(title="Activity API (SQLite, no ORM)")

DB_PATH = "activity.db"

# ===============================================================
# ENUMS
# ===============================================================

class DayOfWeekEnum(str, enum.Enum):
    ALL = "ALL"
    Sunday = "Sunday"
    Monday = "Monday"
    Tuesday = "Tuesday"
    Wednesday = "Wednesday"
    Thursday = "Thursday"
    Friday = "Friday"
    Saturday = "Saturday"


class PersonFamilyEnum(str, enum.Enum):
    ALL = "ALL"
    TATA = "TATA"
    MAMA = "MAMA"
    GOSIA = "GOSIA"
    EMILKA = "EMILKA"
    RODZINA = "RODZINA"


class ActivityNameEnum(str, enum.Enum):
    All = "All"
    Sprzatanie_kuchni = "Sprzatanie_kuchni"
    Sprzatanie_lazienki = "Sprzatanie_lazienki"
    Zamiatanie_pokoji = "Zamiatanie_pokoji"
    Pranie = "Pranie"
    Odrabianie_lekcji = "Odrabianie_lekcji"
    Basen = "Basen"
    Wstazka = "Wstazka"
    Bajki = "Bajki"
    Czas_spac = "Czas_spac"
    Czas_do_pracy = "Czas_do_pracy"
    Rysowanie = "Rysowanie"
    Obiad = "Obiad"
    Czas_tylko_taty = "Czas_tylko_taty"
    Czas_tylko_mamy = "Czas_tylko_mamy"
    Spacer = "Spacer"
    Gry_i_zabawy = "Gry_i_zabawy"
    Kolacja = "Kolacja"
    Malowanie = "Malowanie"
    Cwiczenia_fizyczne = "Cwiczenia_fizyczne"
    Czas_z_mama = "Czas_z_mama"
    Czas_z_tata = "Czas_z_tata"
    Tance = "Tance"


# ===============================================================
# MAPOWANIA INT -> ENUM
# ===============================================================

DAY_MAP = {
    1: DayOfWeekEnum.Sunday,
    2: DayOfWeekEnum.Monday,
    3: DayOfWeekEnum.Tuesday,
    4: DayOfWeekEnum.Wednesday,
    5: DayOfWeekEnum.Thursday,
    6: DayOfWeekEnum.Friday,
    7: DayOfWeekEnum.Saturday,
}

PERSON_MAP = {
    1: PersonFamilyEnum.TATA,
    2: PersonFamilyEnum.MAMA,
    3: PersonFamilyEnum.GOSIA,
    4: PersonFamilyEnum.EMILKA,
    5: PersonFamilyEnum.RODZINA,
}

ACTIVITY_MAP = {
    1: ActivityNameEnum.Sprzatanie_kuchni,
    2: ActivityNameEnum.Sprzatanie_lazienki,
    3: ActivityNameEnum.Zamiatanie_pokoji,
    4: ActivityNameEnum.Pranie,
    5: ActivityNameEnum.Odrabianie_lekcji,
    6: ActivityNameEnum.Basen,
    7: ActivityNameEnum.Wstazka,
    8: ActivityNameEnum.Bajki,
    9: ActivityNameEnum.Czas_spac,
    10: ActivityNameEnum.Czas_do_pracy,
    11: ActivityNameEnum.Rysowanie,
    12: ActivityNameEnum.Obiad,
    13: ActivityNameEnum.Czas_tylko_taty,
    14: ActivityNameEnum.Czas_tylko_mamy,
    15: ActivityNameEnum.Spacer,
    16: ActivityNameEnum.Gry_i_zabawy,
    17: ActivityNameEnum.Kolacja,
    18: ActivityNameEnum.Malowanie,
    19: ActivityNameEnum.Cwiczenia_fizyczne,
    20: ActivityNameEnum.Czas_z_mama,
    21: ActivityNameEnum.Czas_z_tata,
    22: ActivityNameEnum.Tance,
}


# ===============================================================
# PYDANTIC MODELS
# ===============================================================

class PersonFamilyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    PersonPicture: Optional[str]
    PersonName: PersonFamilyEnum


class PictureActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    ActivityName: ActivityNameEnum
    Picture: Optional[str]


class ActivityDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    CreatedAt: datetime
    StartTime: timedelta
    EndTime: timedelta
    Description: Optional[str]
    DayOfWeek: DayOfWeekEnum
    ModelPersonFamily: Optional[PersonFamilyOut]
    ModelPictureActivity: Optional[PictureActivityOut]


# ===============================================================
# SQLITE
# ===============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def seconds_to_timedelta(seconds: int) -> timedelta:
    return timedelta(seconds=seconds)


# ===============================================================
# ENDPOINTS
# ===============================================================

@app.get("/activitydays/", response_model=List[ActivityDayOut])
def get_all_activity_days():
    db = get_db()

    rows = db.execute("""
        SELECT
            ad.Id,
            ad.CreatedAt,
            ad.StartTime,
            ad.EndTime,
            ad.Description,
            ad.DayOfWeek,

            pf.Id AS pf_id,
            pf.PersonName,
            pf.PersonPicture,

            pa.Id AS pa_id,
            pa.ActivityName,
            pa.Picture

        FROM ActiviesDays ad
        LEFT JOIN PersonFamilies pf ON pf.Id = ad.ModelPersonFamilyId
        LEFT JOIN PictureActivities pa ON pa.Id = ad.ModelPictureActivityId
        ORDER BY ad.Id
    """).fetchall()

    result = []

    for r in rows:
        result.append(ActivityDayOut(
            Id=r["Id"],
            CreatedAt=datetime.fromisoformat(r["CreatedAt"]),
            StartTime=seconds_to_timedelta(r["StartTime"]),
            EndTime=seconds_to_timedelta(r["EndTime"]),
            Description=r["Description"],
            DayOfWeek=DAY_MAP.get(r["DayOfWeek"], DayOfWeekEnum.ALL),

            ModelPersonFamily=PersonFamilyOut(
                Id=r["pf_id"],
                PersonPicture=r["PersonPicture"],
                PersonName=PERSON_MAP.get(r["PersonName"], PersonFamilyEnum.ALL)
            ) if r["pf_id"] else None,

            ModelPictureActivity=PictureActivityOut(
                Id=r["pa_id"],
                ActivityName=ACTIVITY_MAP.get(r["ActivityName"], ActivityNameEnum.All),
                Picture=r["Picture"]
            ) if r["pa_id"] else None
        ))

    db.close()
    return result


@app.get("/activitydays/current", response_model=List[ActivityDayOut])
def get_current_activity_days():
    now = datetime.now()
    weekday = now.isoweekday()
    current_seconds = now.hour * 3600 + now.minute * 60 + now.second

    db = get_db()

    rows = db.execute("""
        SELECT * FROM ActiviesDays
        WHERE DayOfWeek = ?
    """, (weekday,)).fetchall()

    ids = [
        r["Id"]
        for r in rows
        if r["StartTime"] <= current_seconds <= r["EndTime"]
    ]

    db.close()

    if not ids:
        return []

    return get_all_activity_days()


# ===============================================================
# RUN
# ===============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("activity_api:app", host="0.0.0.0", port=8000)
