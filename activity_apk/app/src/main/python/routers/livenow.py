from fastapi import APIRouter, HTTPException, Request, Form, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime

from templates import templates
from validators import (
    system_day_to_db_day,
    hhmm,
    validate_activity_edit_form,
    time_to_minutes,
)
from db import get_db


router = APIRouter(
    prefix="/live",
    tags=["live"]
)


# ============================================================
# POMOCNICZE
# ============================================================

DAY_NAMES = {
    1: "Niedziela",
    2: "Poniedzialek",
    3: "Wtorek",
    4: "Sroda",
    5: "Czwartek",
    6: "Piatek",
    7: "Sobota",
}


def is_time_in_range(start, end, current):
    """
    Sprawdza, czy aktywność jest LIVE.

    Zwykła aktywność:
        08:00 -> 16:00

    Przejście przez północ:
        23:00 -> 06:45

    UWAGA:
    Dla aktywności zapisanej na DZISIAJ 23:00 -> 06:45
    godzina 05:55 NIE jest LIVE.
    O tej godzinie LIVE może być tylko aktywność z dnia poprzedniego.
    """

    start_min = time_to_minutes(start)
    end_min = time_to_minutes(end)
    current_min = time_to_minutes(current)

    if start_min <= end_min:
        return start_min <= current_min <= end_min

    # Aktywność przechodząca przez północ.
    # Jest LIVE tylko po godzinie startu tego dnia.
    return current_min >= start_min


def is_cross_midnight(start, end):
    """Czy aktywność przechodzi przez północ."""
    return time_to_minutes(start) > time_to_minutes(end)


def get_previous_day(current_day_iso):
    """
    current_day_iso:
        Monday = 1
        ...
        Sunday = 7

    Zwraca dzień DB poprzedniego dnia.
    """
    previous_iso_day = 7 if current_day_iso == 1 else current_day_iso - 1
    return system_day_to_db_day(previous_iso_day)


def get_current_day_info():
    now = datetime.now()

    iso_day = now.isoweekday()
    current_day = system_day_to_db_day(iso_day)
    previous_day = get_previous_day(iso_day)

    current_time = now.strftime("%H:%M:%S")

    return (
        now,
        iso_day,
        current_day,
        previous_day,
        current_time,
    )


# ============================================================
# LISTA LIVE NOW
# ============================================================

@router.get("/now", response_class=HTMLResponse)
def livenow_page(
    request: Request,
    person: str = Query(default=""),
    db=Depends(get_db)
):
    cursor = db.cursor()
    (now, iso_day, current_day, previous_day, current_time) = get_current_day_info()

    base = """
        SELECT ad.StartTime, ad.EndTime, ad.Description,
               pf.PersonName, pf.PersonPicture, pa.Picture
        FROM ActiviesDays ad
        LEFT JOIN PersonFamilies pf ON ad.ModelPersonFamilyId = pf.Id
        LEFT JOIN PictureActivities pa ON ad.ModelPictureActivityId = pa.Id
        WHERE ad.DayOfWeek = ?
    """
    today = cursor.execute(
        base + " ORDER BY ad.StartTime", (current_day,)).fetchall()
    prev = cursor.execute(
        base + " AND time(ad.StartTime) > time(ad.EndTime)"
               " AND time(ad.EndTime) >= time(?) ORDER BY ad.StartTime",
        (previous_day, current_time)).fetchall()
    persons = [
        r["PersonName"].upper() for r in cursor.execute(
            "SELECT PersonName FROM PersonFamilies ORDER BY Id").fetchall()
    ]
    db.close()

    selected = person.upper() if person.upper() in persons else ""

    def item(r):
        return {
            "person": r["PersonName"],
            "description": r["Description"],
            "picture": r["Picture"],
            "personPicture": r["PersonPicture"],
            "start": r["StartTime"],
            "end": r["EndTime"],
        }

    def wanted(r):
        return not selected or (r["PersonName"] or "").upper() == selected

    live_items = [item(r) for r in prev if wanted(r)]
    next_by_person = {}
    cur_min = time_to_minutes(current_time)

    for r in today:
        if not wanted(r):
            continue
        if is_time_in_range(r["StartTime"], r["EndTime"], current_time):
            live_items.append(item(r))
        elif time_to_minutes(r["StartTime"]) > cur_min:
            next_by_person.setdefault(r["PersonName"], item(r))

    live_items.sort(key=lambda x: x["start"])
    next_items = sorted(next_by_person.values(), key=lambda x: x["start"])

    return templates.TemplateResponse(
        request,
        "livenow.html",
        {
            "live_items": live_items,
            "next_items": next_items,
            "persons": persons,
            "selected": selected,
            "now": current_time,
        }
    )


@router.get("/status")
def status_redirect(person: str = Query(default="")):
    from fastapi.responses import RedirectResponse
    url = "/live/now" + (f"?person={person}" if person else "")
    return RedirectResponse(url, status_code=302)


# ============================================================
# STATUS ALL
# ============================================================

def _prev_db_day(d):
    return 7 if d == 1 else d - 1


def _now_window_day(today_db_day, cur_min):
    return today_db_day if cur_min >= 360 else _prev_db_day(today_db_day)


def _render_statusall(request, db, day):
    cursor = db.cursor()

    (now, iso_day, today_db_day, _prev, current_time) = get_current_day_info()

    cur_min = time_to_minutes(current_time)
    now_day = _now_window_day(today_db_day, cur_min)
    now_off = (cur_min - 360) % 1440

    if day is None or day < 1 or day > 7:
        day = now_day

    prev_day = _prev_db_day(day)

    rows = cursor.execute("""
        SELECT
            ad.Id, ad.DayOfWeek, ad.StartTime, ad.EndTime, ad.Description,
            pf.Id AS PersonId, pf.PersonName,
            pa.Picture, pa.Name AS ActivityName
        FROM ActiviesDays ad
        LEFT JOIN PersonFamilies pf ON ad.ModelPersonFamilyId = pf.Id
        LEFT JOIN PictureActivities pa ON ad.ModelPictureActivityId = pa.Id
        WHERE ad.DayOfWeek IN (?, ?)
        ORDER BY ad.StartTime
    """, (day, prev_day)).fetchall()

    persons = [
        {"id": r["Id"], "name": r["PersonName"]}
        for r in cursor.execute(
            "SELECT Id, PersonName FROM PersonFamilies ORDER BY Id"
        ).fetchall()
    ]

    pictures = [
        {"id": p["Id"], "label": p["Name"], "picture": p["Picture"]}
        for p in cursor.execute(
            "SELECT Id, Name, Picture FROM PictureActivities"
        ).fetchall()
    ]

    db.close()

    columns = {p["id"]: [] for p in persons}

    for r in rows:
        pid = r["PersonId"]
        if pid not in columns:
            continue

        s = time_to_minutes(r["StartTime"])
        e = time_to_minutes(r["EndTime"])

        dur = (e - s) % 1440 or 1440
        off = (s - 360) % 1440
        end = off + dur

        if r["DayOfWeek"] == prev_day:
            if end <= 1440:
                continue
            segs = [(0, end - 1440)]
        else:
            segs = [(off, min(end, 1440) - off)]

        for a, d in segs:
            columns[pid].append({
                "activity_id": r["Id"],
                "description": r["Description"],
                "picture": r["Picture"],
                "activityname": r["ActivityName"],
                "person_id": pid,
                "start": r["StartTime"],
                "end": r["EndTime"],
                "day": r["DayOfWeek"],
                "label": f'{hhmm(r["StartTime"])}–{hhmm(r["EndTime"])}',
                "top": round(a / 14.4, 3),
                "height": round(d / 14.4, 3),
                "is_live": day == now_day and a <= now_off < a + d,
            })

    return templates.TemplateResponse(
        request,
        "statusall.html",
        {
            "columns": columns,
            "persons": persons,
            "pictures": pictures,
            "hours": [f"{(6 + 2 * i) % 24:02d}:00" for i in range(12)],
            "now_pct": round(now_off / 14.4, 3) if day == now_day else None,
            "day_name": DAY_NAMES.get(day, ""),
            "day_index": day,
            "now": current_time,
        }
    )


@router.get("/statusall", response_class=HTMLResponse)
def statusall_page(request: Request, db=Depends(get_db)):
    return _render_statusall(request, db, None)


@router.get("/liveall/{day}", response_class=HTMLResponse)
def statusall_by_day(request: Request, day: int, db=Depends(get_db)):
    return _render_statusall(request, db, day)


# ============================================================
# STATUS ALL TV
# ============================================================

def _build_tv_context(db, day):
    cursor = db.cursor()
    (now, iso_day, today_db_day, previous_day, current_time) = get_current_day_info()

    if day is None or day < 1 or day > 7:
        day = today_db_day

    base = """
        SELECT ad.Id, ad.StartTime, ad.EndTime, ad.Description,
               pf.Id AS PersonId, pa.Picture, pa.Name AS ActivityName
        FROM ActiviesDays ad
        LEFT JOIN PersonFamilies pf ON ad.ModelPersonFamilyId = pf.Id
        LEFT JOIN PictureActivities pa ON ad.ModelPictureActivityId = pa.Id
        WHERE ad.DayOfWeek = ?
    """
    rows = cursor.execute(base + " ORDER BY ad.StartTime", (day,)).fetchall()

    rows_prev = []
    if day == today_db_day:
        rows_prev = cursor.execute(
            base + " AND time(ad.StartTime) > time(ad.EndTime)"
                   " AND time(ad.EndTime) >= time(?) ORDER BY ad.StartTime",
            (previous_day, current_time),
        ).fetchall()

    persons = [
        {"id": r["Id"], "name": r["PersonName"]}
        for r in cursor.execute(
            "SELECT Id, PersonName FROM PersonFamilies ORDER BY Id"
        ).fetchall()
    ]
    pictures = [
        {"id": p["Id"], "label": p["Name"], "picture": p["Picture"]}
        for p in cursor.execute(
            "SELECT Id, Name, Picture FROM PictureActivities"
        ).fetchall()
    ]
    db.close()

    table = {}

    def put(r, live):
        key = f'{hhmm(r["StartTime"])} – {hhmm(r["EndTime"])}'
        row = table.setdefault(key, {p["id"]: None for p in persons})
        if r["PersonId"] in row:
            row[r["PersonId"]] = {
                "activity_id": r["Id"],
                "description": r["Description"],
                "picture": r["Picture"],
                "activityname": r["ActivityName"],
                "person_id": r["PersonId"],
                "start": r["StartTime"],
                "end": r["EndTime"],
                "is_live": live,
            }

    for r in rows:
        live = day == today_db_day and is_time_in_range(
            r["StartTime"], r["EndTime"], current_time)
        put(r, live)
    for r in rows_prev:
        put(r, True)

    return {
        "table": table,
        "persons": persons,
        "day_name": DAY_NAMES.get(day, ""),
        "day_index": day,
        "pictures": pictures,
        "now": current_time,
    }


@router.get("/statusalltv", response_class=HTMLResponse)
def statusalltv_page(request: Request, db=Depends(get_db)):
    return templates.TemplateResponse(
        request, "statusalltv.html", _build_tv_context(db, None))


@router.get("/livealltv/{day}", response_class=HTMLResponse)
def statusall_by_day_tv(request: Request, day: int, db=Depends(get_db)):
    return templates.TemplateResponse(
        request, "statusalltv.html", _build_tv_context(db, day))


# ============================================================
# EDIT ACTIVITY
# ============================================================

@router.put("/statusall/edit/{activity_id}", response_class=HTMLResponse)
def edit_activity_put(
    activity_id: int,
    start: str = Form(...),
    end: str = Form(...),
    description: str = Form(""),
    activityname: str = Form(""),
    day: int = Form(...),
    person_id: int = Form(...),
    db=Depends(get_db)
):

    cursor = db.cursor()

    # ========================================================
    # ŹRÓDŁO PRAWDY
    # ========================================================

    activity = cursor.execute("""
        SELECT
            DayOfWeek,
            ModelPersonFamilyId
        FROM ActiviesDays
        WHERE Id = ?
    """, (activity_id,)).fetchone()

    if not activity:
        db.close()

        raise HTTPException(
            status_code=404,
            detail="Aktywność nie istnieje"
        )

    old_day_of_week = activity["DayOfWeek"]
    old_person_id = activity["ModelPersonFamilyId"]

    # ========================================================
    # WALIDACJA DNIA
    # ========================================================

    if day < 1 or day > 7:

        db.close()

        return JSONResponse(
            {
                "status": "error",
                "errors": [
                    "Nieprawidłowy dzień tygodnia"
                ]
            },
            status_code=400
        )

    # ========================================================
    # CZASY
    # ========================================================

    start = hhmm(start)
    end = hhmm(end)

    new_person_id = person_id

    # ========================================================
    # WALIDACJA
    # ========================================================

    errors = validate_activity_edit_form(
        start=start,
        end=end,
        day_of_week=day,
        person_id=new_person_id,
        activity_id=activity_id,
        db=db,
    )

    if errors:

        db.close()

        return JSONResponse(
            {
                "status": "error",
                "errors": errors
            },
            status_code=400
        )

    # ========================================================
    # AKTYWNOŚĆ -> ID OBRAZKA
    # ========================================================

    picture_id = None

    if activityname:

        pic = cursor.execute("""
            SELECT Id
            FROM PictureActivities
            WHERE Name = ?
        """, (activityname,)).fetchone()

        if pic:
            picture_id = pic["Id"]

    # ========================================================
    # UPDATE
    # ========================================================

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
        day,
        start,
        end,
        description.strip() or None,
        person_id,
        picture_id,
        activity_id
    ))

    db.commit()
    db.close()

    return JSONResponse({
        "status": "ok"
    })
