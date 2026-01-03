from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from pathlib import Path
import enum
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER


app = FastAPI()

# ---------- PATHS ----------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "activity.db"

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------- DAY NAMES ----------
DAY_NAMES = {
    0: "ALL",
    1: "Niedziela",
    2: "Poniedzialek",
    3: "Wtorek",
    4: "Sroda",
    5: "Czwartek",
    6: "Piatek",
    7: "Sobota",
}

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

PERSON_ENUM_MAP = {
    0: PersonFamilyEnum.ALL,
    1: PersonFamilyEnum.TATA,
    2: PersonFamilyEnum.MAMA,
    3: PersonFamilyEnum.GOSIA,
    4: PersonFamilyEnum.EMILKA,
    5: PersonFamilyEnum.RODZINA,
}

ACTIVITY_ENUM_MAP = {
            1: ActivityNameEnum.All,
                2: ActivityNameEnum.Sprzatanie_kuchni,
                    3: ActivityNameEnum.Sprzatanie_lazienki,
                        4: ActivityNameEnum.Zamiatanie_pokoji,
                            5: ActivityNameEnum.Pranie,
                                6: ActivityNameEnum.Odrabianie_lekcji,
                                    7: ActivityNameEnum.Basen,
                                        8: ActivityNameEnum.Wstazka,
                                            9: ActivityNameEnum.Bajki,
                                                10: ActivityNameEnum.Czas_spac,
                                                    11: ActivityNameEnum.Czas_do_pracy,
                                                        12: ActivityNameEnum.Rysowanie,
                                                            13: ActivityNameEnum.Obiad,
                                                                14: ActivityNameEnum.Czas_tylko_taty,
                                                                    15: ActivityNameEnum.Czas_tylko_mamy,
                                                                        16: ActivityNameEnum.Spacer,
                                                                            17: ActivityNameEnum.Gry_i_zabawy,
                                                                                18: ActivityNameEnum.Kolacja,
                                                                                    19: ActivityNameEnum.Malowanie,
                                                                                        20: ActivityNameEnum.Cwiczenia_fizyczne,
                                                                                            21: ActivityNameEnum.Czas_z_mama,
                                                                                                22: ActivityNameEnum.Czas_z_tata,
                                                                                                    23: ActivityNameEnum.Tance,
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


@app.get("/activities/add", response_class=HTMLResponse)
def add_activity_form(request: Request):
    return templates.TemplateResponse(
        "activity_add.html",
        {
            "request": request,
            "persons": PERSON_ENUM_MAP,
            "activities": ACTIVITY_ENUM_MAP,
            "days": {
                "MONDAY": "Poniedziałek",
                "TUESDAY": "Wtorek",
                "WEDNESDAY": "Środa",
                "THURSDAY": "Czwartek",
                "FRIDAY": "Piątek",
                "SATURDAY": "Sobota",
                "SUNDAY": "Niedziela",
            }
        }
    )


@app.post("/activities/add")
def add_activity_post(
    start: str = Form(...),
    end: str = Form(...),
    day_of_week: str = Form(...),     # ✅ DODANE
    description: str = Form(""),
    person_id: int = Form(...),
    picture_id: int = Form(...)
):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO ActiviesDays (
            DayOfWeek,
            StartTime,
            EndTime,
            Description,
            ModelPersonFamilyId,
            ModelPictureActivityId
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        day_of_week,
        start,
        end,
        description,
        person_id,
        picture_id
    ))

    db.commit()
    db.close()

    return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)


@app.get("/edit/{activity_id}", response_class=HTMLResponse)
def edit_activity_page(request: Request, activity_id: int):
    db = get_db()
    cursor = db.cursor()

    activity = cursor.execute("""
        SELECT
            Id,
            StartTime,
            EndTime,
            Description,
            ModelPersonFamilyId,
            ModelPictureActivityId
        FROM ActiviesDays
        WHERE Id = ?
    """, (activity_id,)).fetchone()

    if not activity:
        db.close()
        return HTMLResponse("Nie znaleziono aktywności", status_code=404)

    # --- OSOBY ---
    persons_raw = cursor.execute("""
        SELECT Id, PersonName
        FROM PersonFamilies
    """).fetchall()

    persons = []
    for p in persons_raw:
        enum_val = PERSON_ENUM_MAP.get(p["PersonName"])
        persons.append({
            "id": p["Id"],
            "label": enum_val.value if enum_val else "Nieznana"
        })

    # --- AKTYWNOŚCI ---
    pictures_raw = cursor.execute("""
        SELECT Id, ActivityName, Picture
        FROM PictureActivities
    """).fetchall()

    pictures = []
    for pic in pictures_raw:
        enum_val = ACTIVITY_ENUM_MAP.get(pic["ActivityName"])
        pictures.append({
            "id": pic["Id"],
            "label": enum_val.value if enum_val else "Nieznana",
            "picture": pic["Picture"]
        })

    db.close()

    return templates.TemplateResponse(
        "edit_activity.html",
        {
            "request": request,
            "activity": activity,
            "persons": persons,
            "pictures": pictures,
        }
    )


@app.post("/edit/{activity_id}")
def edit_activity_post(
    activity_id: int,
    start: str = Form(...),
    end: str = Form(...),
    description: str = Form(""),
    person_id: int = Form(...),
    picture_id: int = Form(...)
):
    db = get_db()
    cursor = db.cursor()

    # sprawdzamy czy rekord istnieje
    existing = cursor.execute(
        "SELECT Id FROM ActiviesDays WHERE Id = ?",
        (activity_id,)
    ).fetchone()

    if not existing:
        db.close()
        return HTMLResponse("Nie znaleziono aktywności", status_code=404)

    # update
    cursor.execute("""
        UPDATE ActiviesDays
        SET
            StartTime = ?,
            EndTime = ?,
            Description = ?,
            ModelPersonFamilyId = ?,
            ModelPictureActivityId = ?
        WHERE Id = ?
    """, (
        start,
        end,
        description,
        person_id,
        picture_id,
        activity_id
    ))

    db.commit()
    db.close()

    return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)

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
    current_day_name = now.strftime("%A")
    current_time = now.strftime("%H:%M:%S")  # HH:MM:SS

    #current_day mam 6 a u mnie to piatek z enum musze tu podmienic bo baze mam zrobiona wg moich dni
    current_day = current_day + 1

    rows = cursor.execute("""
        SELECT
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
            "current_day_name" : current_day_name,
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
        {
            "request": request,
            "week": week,
            "day_names": DAY_NAMES,   # 👈 KLUCZOWE
        }
    )
 


@app.get("/api/pictureactivities")
def get_picture_activities():
    db = get_db()
    cursor = db.cursor()

    rows = cursor.execute("""
        SELECT
            Id,
            ActivityName,
            Picture
        FROM PictureActivities
        ORDER BY Id
    """).fetchall()

    db.close()

    result = []

    for r in rows:
        enum_value = ACTIVITY_ENUM_MAP.get(r["ActivityName"])
        activity_name = enum_value.value if enum_value else None

        result.append({
            "id": r["Id"],
            "activityName": activity_name,
            "picture": r["Picture"],
        })

    return result   


# ---------- PICTURE ACTIVITIES UI ----------
@app.get("/pictureactivities", response_class=HTMLResponse)
def picture_activities_page(request: Request):
    db = get_db()
    cursor = db.cursor()

    rows = cursor.execute("""
        SELECT
            Id,
            ActivityName,
            Picture
        FROM PictureActivities
        ORDER BY Id
    """).fetchall()

    db.close()

    items = []

    for r in rows:
        enum_value = ACTIVITY_ENUM_MAP.get(r["ActivityName"])
        activity_name = enum_value.value if enum_value else "Nieznana"

        items.append({
            "id": r["Id"],
            "activityName": activity_name,
            "picture": r["Picture"],
        })

    return templates.TemplateResponse(
        "pictureactivities.html",
        {
            "request": request,
            "items": items
        }
    )



# ---------- EDIT PICTURE ACTIVITY ----------
@app.get("/pictureactivities/edit/{item_id}", response_class=HTMLResponse)
def edit_picture_activity_form(item_id: int, request: Request):
    db = get_db()
    cursor = db.cursor()

    row = cursor.execute("""
        SELECT Id, ActivityName, Picture
        FROM PictureActivities
        WHERE Id = ?
    """, (item_id,)).fetchone()

    db.close()

    if not row:
        return HTMLResponse("Nie znaleziono rekordu", status_code=404)

    return templates.TemplateResponse(
        "pictureactivity_edit.html",
        {
            "request": request,
            "item": {
                "id": row["Id"],
                "activityName": row["ActivityName"],
                "picture": row["Picture"]
            },
            "activities": ACTIVITY_ENUM_MAP
        }
    )


@app.post("/pictureactivities/edit/{item_id}")
def edit_picture_activity_save(
    item_id: int,
    activityName: int = Form(...),
    picture: str = Form("")
):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE PictureActivities
        SET ActivityName = ?, Picture = ?
        WHERE Id = ?
    """, (activityName, picture, item_id))

    db.commit()
    db.close()

    return RedirectResponse(
        url="/pictureactivities",
        status_code=303
    )    
