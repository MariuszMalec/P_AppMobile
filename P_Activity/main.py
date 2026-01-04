from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from pathlib import Path
import enum, re
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER


app = FastAPI()

# ---------- PATHS ----------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "activity.db"

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))



# --------- Walidacje pomocnicze ----------
TIME_RE = re.compile(r"^\d{2}:\d{2}$")

def time_to_minutes(value: str) -> int:
    # value: "11:58" albo "12:58"
    t = datetime.strptime(value, "%H:%M")
    return t.hour * 60 + t.minute

    raise ValueError(f"Nieprawidłowy format czasu: {value}")

def validate_activity_form(
    start: str,
    end: str,
    day_of_week: int,
    person_id: int,
    picture_name: str
) -> list[str]:
    errors = []

    # --- czas ---
    if not TIME_RE.match(start):
        errors.append("StartTime musi być w formacie HH:MM")

    if not TIME_RE.match(end):
        errors.append("EndTime musi być w formacie HH:MM")

    if TIME_RE.match(start) and TIME_RE.match(end):

        try:
            start_min = time_to_minutes(start)
            end_min = time_to_minutes(end)
        except ValueError as e:
            errors.append(str(e))


        print(start_min)
        print(end_min)

        # ✅ TU JEST WŁAŚCIWA WALIDACJA
        if not errors and start_min >= end_min:
            errors.append("Godzina startu musi być wcześniejsza niż zakończenia")


    # --- dzień ---
    if day_of_week not in DAY_NAMES or day_of_week == 0:
        errors.append("Nieprawidłowy dzień tygodnia")

    # --- enumy ---
    if person_id not in PERSON_ENUM_MAP:
        errors.append("Nieprawidłowa osoba")

    if picture_name is None:
        errors.append("Nieprawidłowa aktywność")

    return errors

def validate_activity_edit_form(
    start: str,
    end: str,
    day_of_week: int,
    person_id: int,
) -> list[str]:
    errors = []

    # --- czas ---
    if not TIME_RE.match(start):
        errors.append("StartTime musi być w formacie HH:MM")

    if not TIME_RE.match(end):
        errors.append("EndTime musi być w formacie HH:MM")

    if TIME_RE.match(start) and TIME_RE.match(end):

        try:
            start_min = time_to_minutes(start)
            end_min = time_to_minutes(end)
        except ValueError as e:
            errors.append(str(e))


        print(start_min)
        print(end_min)

        # ✅ TU JEST WŁAŚCIWA WALIDACJA
        if not errors and start_min >= end_min:
            errors.append("Godzina startu musi być wcześniejsza niż zakończenia")


    # --- dzień ---
    if day_of_week not in DAY_NAMES or day_of_week == 0:
        errors.append("Nieprawidłowy dzień tygodnia")

    # --- enumy ---
    if person_id not in PERSON_ENUM_MAP:
        errors.append("Nieprawidłowa osoba")


    return errors



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

def system_day_to_db_day(iso_day: int) -> int:
    # iso: 1=Mon ... 7=Sun
    # db : 1=Sun ... 7=Sat
    return 1 if iso_day == 7 else iso_day + 1


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
    Test = "Test"

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
                                                                                                    24: ActivityNameEnum.Test,
                                                                                                    }

# ---------- DB ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- MAIN PAGE ----------
@app.get("/")
def root_redirect():
    return RedirectResponse("/panel_user", status_code=302) #/livenow


##  Panel user only
@app.get("/panel_user", response_class=HTMLResponse)
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
        "panel_user.html",
        {
            "request": request,
            "days": grouped_days
        }
    )


























@app.get("/activities", response_class=HTMLResponse)
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
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT Id, ActivityName, Name, Picture
        FROM PictureActivities
        ORDER BY Name
    """)
    activities = cursor.fetchall()
    db.close()

    return templates.TemplateResponse(
        "activity_add.html",
        {
            "request": request,
            "persons": PERSON_ENUM_MAP,
            "activities": activities,
            "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
        }
    )


@app.post("/activities/add", response_class=HTMLResponse)
def add_activity_post(
    request: Request,
    start: str = Form(...),
    end: str = Form(...),
    day_of_week: int = Form(...),
    description: str = Form(""),
    person_id: int = Form(...),
    activity_name: str = Form(...)
):
    errors = validate_activity_form(
        start, end, day_of_week, person_id, activity_name
    )

    db = get_db()
    cursor = db.cursor()

    # 🔁 ZAWSZE pobieramy aktywności (potrzebne przy błędzie)
    cursor.execute("SELECT Id, Name FROM PictureActivities ORDER BY Name")
    activities = cursor.fetchall()

    # ❌ BŁĘDY → wracamy do formularza
    if errors:
        db.close()
        return templates.TemplateResponse(
            "activity_add.html",
            {
                "request": request,
                "errors": errors,
                "form": {
                    "start": start,
                    "end": end,
                    "day_of_week": day_of_week,
                    "description": description,
                    "person_id": person_id,
                    "activity_name": activity_name,
                },
                "persons": PERSON_ENUM_MAP,
                "activities": activities,   # 🔴 TO BYŁ BRAK
                "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
            },
            status_code=400
        )

    # ✅ Szukamy obrazka po Name
    cursor.execute(
        "SELECT Id FROM PictureActivities WHERE Name = ?",
        (activity_name,)
    )
    row = cursor.fetchone()

    if not row:
        db.close()
        return templates.TemplateResponse(
            "activity_add.html",
            {
                "request": request,
                "errors": ["Nieprawidłowa aktywność"],
                "persons": PERSON_ENUM_MAP,
                "activities": activities,
                "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
            },
            status_code=400
        )

    picture_id = row["Id"]

    # ✅ INSERT
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
        description.strip() or None,
        5 if person_id == 0 else person_id,  # ✅ JEDYNA ZMIANA
        picture_id
    ))

    db.commit()
    db.close()

    return RedirectResponse("/", status_code=303)



@app.get("/activities/edit/{activity_id}", response_class=HTMLResponse)
def edit_activity_page(request: Request, activity_id: int):
    db = get_db()
    cursor = db.cursor()

    activity = cursor.execute("""
        SELECT
            Id,
            DayOfWeek,
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

    # --- AKTYWNOŚCI (POPRAWKA) ---
    pictures_raw = cursor.execute("""
        SELECT Id, Name, Picture
        FROM PictureActivities
    """).fetchall()

    pictures = []
    for pic in pictures_raw:
        pictures.append({
            "id": pic["Id"],
            "label": pic["Name"],       # ✅ BEZ ENUM
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
            "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
        }
    )



@app.post("/activities/edit/{activity_id}", response_class=HTMLResponse)
def edit_activity_post(
    request: Request,
    activity_id: int,
    day_of_week: int = Form(...),
    start: str = Form(...),
    end: str = Form(...),
    description: str = Form(""),
    person_id: int = Form(...),
    picture_id: int = Form(...)
):
    errors = validate_activity_edit_form(
        start, end, day_of_week, person_id
    )

    db = get_db()
    cursor = db.cursor()

    # --- pobieramy aktywność (potrzebna przy błędach) ---
    activity = cursor.execute("""
        SELECT
            Id,
            DayOfWeek,
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
        SELECT Id, Name, Picture
        FROM PictureActivities
    """).fetchall()

    pictures = []
    for pic in pictures_raw:
        pictures.append({
            "id": pic["Id"],
            "label": pic["Name"],
            "picture": pic["Picture"]
        })

    # ❌ BŁĘDY → wracamy do formularza
    if errors:
        db.close()
        return templates.TemplateResponse(
            "edit_activity.html",
            {
                "request": request,
                "errors": errors,
                "activity": {
                    "Id": activity_id,
                    "DayOfWeek": day_of_week,
                    "StartTime": start,
                    "EndTime": end,
                    "Description": description,
                    "ModelPersonFamilyId": person_id,
                    "ModelPictureActivityId": picture_id,
                },
                "persons": persons,
                "pictures": pictures,
                "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
            },
            status_code=400
        )

    # ✅ UPDATE
    cursor.execute("""
        UPDATE ActiviesDays
        SET
            DayOfWeek = ?,
            StartTime = ?,
            EndTime = ?,
            Description = ?,
            ModelPersonFamilyId = ?,
            ModelPictureActivityId = ?
        WHERE Id = ?
    """, (
        day_of_week,
        start,
        end,
        description.strip() or None,
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
    iso_day = now.isoweekday()          # 1-7
    current_day = system_day_to_db_day(iso_day)

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
    iso_day = now.isoweekday()          # 1-7
    current_day = system_day_to_db_day(iso_day)
    current_day_name = now.strftime("%A")
    current_time = now.strftime("%H:%M:%S")  # HH:MM:SS

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


@app.get("/statusall", response_class=HTMLResponse)
def statusall_page(request: Request):
    db = get_db()
    cursor = db.cursor()

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    iso_day = now.isoweekday()
    current_day = system_day_to_db_day(iso_day)
    current_day_name = now.strftime("%A")

    rows = cursor.execute("""
        SELECT
            ad.StartTime,
            ad.EndTime,
            ad.Description,
            pf.Id AS PersonId,
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

    persons = [
        {"id": 3, "name": "GOSIA"},
        {"id": 2, "name": "MAMA"},
        {"id": 1, "name": "TATA"},
        {"id": 4, "name": "EMILKA"},
        {"id": 5, "name": "ALL"},
    ]

    table = {}

    for r in rows:
        time_key = f'{r["StartTime"]} – {r["EndTime"]}'

        if time_key not in table:
            table[time_key] = {p["id"]: None for p in persons}

        person_id = r["PersonId"]   # 🔥 KLUCZOWA LINIA

        if person_id in table[time_key]:
            table[time_key][person_id] = {
                "description": r["Description"],
                "picture": r["Picture"],
                "is_live": r["StartTime"] <= current_time <= r["EndTime"]
            }

    return templates.TemplateResponse(
        "statusall.html",
        {
            "request": request,
            "table": table,
            "persons": persons,
            "day_name": current_day_name,
            "now": current_time,
        }
    )


@app.get("/statusalltv", response_class=HTMLResponse)
def statusalltv_page(request: Request):
    db = get_db()
    cursor = db.cursor()

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    iso_day = now.isoweekday()
    current_day = system_day_to_db_day(iso_day)
    current_day_name = now.strftime("%A")

    rows = cursor.execute("""
        SELECT
            ad.StartTime,
            ad.EndTime,
            ad.Description,
            pf.Id AS PersonId,
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

    persons = [
        {"id": 3, "name": "GOSIA"},
        {"id": 2, "name": "MAMA"},
        {"id": 1, "name": "TATA"},
        {"id": 4, "name": "EMILKA"},
        {"id": 5, "name": "ALL"},
    ]

    table = {}

    for r in rows:
        time_key = f'{r["StartTime"]} – {r["EndTime"]}'

        if time_key not in table:
            table[time_key] = {p["id"]: None for p in persons}

        person_id = r["PersonId"]   # 🔥 KLUCZOWA LINIA

        if person_id in table[time_key]:
            table[time_key][person_id] = {
                "description": r["Description"],
                "picture": r["Picture"],
                "is_live": r["StartTime"] <= current_time <= r["EndTime"]
            }

    return templates.TemplateResponse(
        "statusalltv.html",
        {
            "request": request,
            "table": table,
            "persons": persons,
            "day_name": current_day_name,
            "now": current_time,
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
            Name,
            Picture
        FROM PictureActivities
        ORDER BY Id
    """).fetchall()

    db.close()

    items = []

    for r in rows:
        items.append({
            "id": r["Id"],
            "activityName": r["Name"],   # ✅ TYLKO Name
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
        SELECT Id, Name, Picture
        FROM PictureActivities
        WHERE Id = ?
    """, (item_id,)).fetchone()

    if not row:
        db.close()
        return HTMLResponse("Nie znaleziono rekordu", status_code=404)

    db.close()

    return templates.TemplateResponse(
        "pictureactivity_edit.html",
        {
            "request": request,
            "item": {
                "id": row["Id"],
                "name": row["Name"],          # ✅ STRING
                "picture": row["Picture"]
            },
            "activities": ACTIVITY_ENUM_MAP  # tylko do listy opcji
        }
    )



@app.post("/pictureactivities/edit/{item_id}")
def edit_picture_activity_save(
    item_id: int,
    name: str = Form(...),      # ✅ STRING
    picture: str = Form("")
):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE PictureActivities
        SET Name = ?, Picture = ?
        WHERE Id = ?
    """, (name, picture, item_id))

    db.commit()
    db.close()

    return RedirectResponse(
        url="/pictureactivities",
        status_code=303
    )

@app.post("/activities/delete/{activity_id}")
def delete_activity(activity_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM ActiviesDays WHERE Id = ?",
        (activity_id,)
    )

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)



# ---------- ADD PICTURE ACTIVITY ----------
@app.get("/pictureactivities/add", response_class=HTMLResponse)
def add_picture_activity_form(request: Request):
    return templates.TemplateResponse(
        "pictureactivity_add.html",
        {
            "request": request,
            "activities": ACTIVITY_ENUM_MAP
        }
    )

@app.post("/pictureactivities/add", response_class=HTMLResponse)
def add_picture_activity_save(
    request: Request,
    activityName: int = Form(...),
    name: str = Form(...),
    picture: str = Form("")
):
    errors = []

    if not name.strip():
        errors.append("Nazwa jest wymagana")

    if errors:
        return templates.TemplateResponse(
            "pictureactivity_add.html",
            {
                "request": request,
                "activities": ACTIVITY_ENUM_MAP,
                "errors": errors,
                "form": {
                    "activityName": activityName,
                    "name": name,
                    "picture": picture,
                }
            }
        )

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO PictureActivities (ActivityName, Name, Picture)
            VALUES (?, ?, ?)
        """, (
            activityName,
            name.strip(),
            picture.strip() or None
        ))

        db.commit()

    except sqlite3.IntegrityError:
        db.close()
        return templates.TemplateResponse(
            "pictureactivity_add.html",
            {
                "request": request,
                "activities": ACTIVITY_ENUM_MAP,
                "errors": ["Ta aktywność MA JUŻ przypisany obrazek"],
                "form": {
                    "activityName": activityName,
                    "name": name,
                    "picture": picture,
                }
            }
        )

    db.close()

    return RedirectResponse(
        url="/pictureactivities",
        status_code=303
    )



@app.get("/livenow", response_class=HTMLResponse)
def livenow_page(request: Request):
    db = get_db()
    cursor = db.cursor()

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    iso_day = now.isoweekday()
    current_day = system_day_to_db_day(iso_day)

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
          AND ad.StartTime <= ?
          AND ad.EndTime >= ?
        ORDER BY ad.StartTime
    """, (current_day, current_time, current_time)).fetchall()

    db.close()

    PERSON_NAME_MAP = {
        1: "TATA",
        2: "MAMA",
        3: "GOSIA",
        4: "EMILKA",
        5: "ALL",
    }


    live_items = []
    for r in rows:
        live_items.append({
            "person": PERSON_NAME_MAP.get(r["PersonName"], ""),
            "description": r["Description"],
            "picture": r["Picture"],
            "personPicture": r["PersonPicture"],
        })


    return templates.TemplateResponse(
        "livenow.html",
        {
            "request": request,
            "live_items": live_items,
            "now": current_time
        }
    )
