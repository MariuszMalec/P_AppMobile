from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from pathlib import Path
import enum


app = FastAPI()

# ---------- PATHS ----------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "activity.db"

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------- DAY NAMES ----------
DAY_NAMES = {
    1: "Poniedziałek",
    2: "Wtorek",
    3: "Środa",
    4: "Czwartek",
    5: "Piątek",
    6: "Sobota",
    7: "Niedziela",
}

class PersonFamilyEnum(str, enum.Enum):
    ALL = "ALL"
    TATA = "TATA"
    MAMA = "MAMA"
    GOSIA = "GOSIA"
    EMILKA = "EMILKA"
    RODZINA = "RODZINA"

PERSON_ENUM_MAP = {
    1: PersonFamilyEnum.TATA,
    2: PersonFamilyEnum.MAMA,
    3: PersonFamilyEnum.GOSIA,
    4: PersonFamilyEnum.EMILKA,
    5: PersonFamilyEnum.RODZINA,
}

# ---------- DB ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- MAIN PAGE ----------
@app.get("/", response_class=HTMLResponse)
def activities_page(request: Request):
    db = get_db()
    cursor = db.cursor()

    query = """
    SELECT
        ad.Id,
        ad.StartTime,
        ad.EndTime,
        ad.Description,
        ad.DayOfWeek,
        pf.PersonName,
        pf.PersonPicture,
        pa.Picture
    FROM ActiviesDays ad
    LEFT JOIN PersonFamilies pf
        ON ad.ModelPersonFamilyId = pf.Id
    LEFT JOIN PictureActivities pa
        ON ad.ModelPictureActivityId = pa.Id
    ORDER BY ad.DayOfWeek, ad.StartTime
    """

    rows = cursor.execute(query).fetchall()
    db.close()

    grouped_days = {}

    for r in rows:
        day = r["DayOfWeek"]

        if day not in grouped_days:
            grouped_days[day] = {
                "dayName": DAY_NAMES.get(day, "Nieznany"),
                "items": []
            }

        # 👉 MAPOWANIE INT → ENUM
        person_label = None
        if r["PersonName"] is not None:
            enum_value = PERSON_ENUM_MAP.get(r["PersonName"])
            if enum_value:
                person_label = enum_value.value  # "TATA", "MAMA", ...

        grouped_days[day]["items"].append({
            "id": r["Id"],
            "start": r["StartTime"],
            "end": r["EndTime"],
            "description": r["Description"],
            "person": person_label,
            "personPicture": r["PersonPicture"],
            "picture": r["Picture"],
        })

    return templates.TemplateResponse(
        "activities.html",
        {
            "request": request,
            "days": grouped_days
        }
    )


@app.get("/edit/{activity_id}", response_class=HTMLResponse)
def edit_activity_page(request: Request, activity_id: int):
    db = get_db()
    cursor = db.cursor()

    activity = cursor.execute("""
        SELECT
            ad.Id,
            ad.StartTime,
            ad.EndTime,
            ad.Description,
            ad.DayOfWeek,
            ad.ModelPersonFamilyId,
            ad.ModelPictureActivityId
        FROM ActiviesDays ad
        WHERE ad.Id = ?
    """, (activity_id,)).fetchone()

    persons = cursor.execute("""
        SELECT Id, PersonName FROM PersonFamilies
    """).fetchall()

    pictures = cursor.execute("""
        SELECT Id, Picture FROM PictureActivities
    """).fetchall()

    db.close()

    if not activity:
        return HTMLResponse("Nie znaleziono aktywności", status_code=404)

    return templates.TemplateResponse(
        "edit_activity.html",
        {
            "request": request,
            "activity": activity,
            "persons": persons,
            "pictures": pictures,
        }
    )



# ---------- API ----------
@app.get("/api/activities")
def api_activities():
    db = get_db()
    cursor = db.cursor()

    rows = cursor.execute("""
        SELECT
            Id,
            StartTime,
            EndTime,
            Description,
            DayOfWeek,
            ModelPersonFamilyId,
            ModelPictureActivityId
        FROM ActiviesDays
        ORDER BY DayOfWeek, StartTime
    """).fetchall()

    db.close()

    return [
        {
            "id": r["Id"],
            "start": r["StartTime"],
            "end": r["EndTime"],
            "description": r["Description"],
            "dayOfWeek": r["DayOfWeek"],
            "personFamilyId": r["ModelPersonFamilyId"],
            "pictureActivityId": r["ModelPictureActivityId"],
        }
        for r in rows
    ]


from datetime import datetime


@app.get("/activitydays/current")
def get_current_activity_day():
    db = get_db()
    cursor = db.cursor()

    now = datetime.now()
    current_day = now.isoweekday()          # 1-7
    current_time = now.strftime("%H:%M:%S") # 'HH:MM:SS'

    query = """
    SELECT
        ad.Id,
        ad.StartTime,
        ad.EndTime,
        ad.Description,
        ad.DayOfWeek,
        pf.PersonName,
        pf.PersonPicture,
        pa.Picture
    FROM ActiviesDays ad
    LEFT JOIN PersonFamilies pf
        ON ad.ModelPersonFamilyId = pf.Id
    LEFT JOIN PictureActivities pa
        ON ad.ModelPictureActivityId = pa.Id
    WHERE ad.DayOfWeek = ?
      AND ad.StartTime <= ?
      AND ad.EndTime >= ?
    ORDER BY ad.StartTime
    """

    rows = cursor.execute(
        query,
        (current_day, current_time, current_time)
    ).fetchall()

    db.close()

    return [
        {
            "id": r["Id"],
            "start": r["StartTime"],
            "end": r["EndTime"],
            "description": r["Description"],
            "dayOfWeek": r["DayOfWeek"],
            "person": r["PersonName"],
            "personPicture": r["PersonPicture"],
            "picture": r["Picture"],
        }
        for r in rows
    ]


from datetime import datetime

@app.get("/status", response_class=HTMLResponse)
def status_page(request: Request):
    db = get_db()
    cursor = db.cursor()

    now = datetime.now()
    current_day = now.isoweekday()          # 1–7
    current_time = now.strftime("%H:%M:%S")  # HH:MM:SS

    rows = cursor.execute("""
        SELECT
            ad.StartTime,
            ad.EndTime,
            ad.Description,
            pf.PersonName,
            pf.PersonPicture,
            pa.Picture
        FROM ActiviesDays ad
        LEFT JOIN PersonFamilies pf
            ON ad.ModelPersonFamilyId = pf.Id
        LEFT JOIN PictureActivities pa
            ON ad.ModelPictureActivityId = pa.Id
        WHERE ad.DayOfWeek = ?
        ORDER BY ad.StartTime
    """, (current_day,)).fetchall()

    db.close()

    current = None
    next_item = None

    for r in rows:
        # 👉 MAPOWANIE ENUM
        person_label = None
        if r["PersonName"] is not None:
            enum_value = PERSON_ENUM_MAP.get(r["PersonName"])
            if enum_value:
                person_label = enum_value.value  # "TATA", "MAMA", itd.

        item = {
            "start": r["StartTime"],
            "end": r["EndTime"],
            "description": r["Description"],
            "person": person_label,
            "personPicture": r["PersonPicture"],
            "picture": r["Picture"],
        }

        if r["StartTime"] <= current_time <= r["EndTime"]:
            current = item
        elif r["StartTime"] > current_time and next_item is None:
            next_item = item

    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
            "now": current_time,
            "current": current,
            "next": next_item,
        }
    )

@app.get("/week", response_class=HTMLResponse)
def week_page(request: Request):
    db = get_db()
    cursor = db.cursor()

    rows = cursor.execute("""
        SELECT
            ad.DayOfWeek,
            ad.StartTime,
            ad.EndTime,
            ad.Description,
            pf.PersonName
        FROM ActiviesDays ad
        LEFT JOIN PersonFamilies pf
            ON ad.ModelPersonFamilyId = pf.Id
        ORDER BY ad.DayOfWeek, ad.StartTime
    """).fetchall()

    db.close()

    week = {}
    for r in rows:
        week.setdefault(r["DayOfWeek"], []).append(r)

    return templates.TemplateResponse(
        "week.html",
        {"request": request, "week": week}
    )    
