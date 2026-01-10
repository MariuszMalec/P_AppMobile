from fastapi import APIRouter, HTTPException, Request, Form, Query, Depends
from fastapi.responses import HTMLResponse
import sqlite3
from db import DB_PATH
from templates import templates
from enums import DAY_NAMES, PERSON_ENUM_MAP
from validators import (    
    system_day_to_db_day,
    hhmm,
    validate_activity_edit_form,
    time_to_minutes,
    normalize_range,
    ranges_overlap
)
from db import get_db
from datetime import datetime
from fastapi.responses import JSONResponse



router = APIRouter(
    prefix="/live",
    tags=["live"]
)


# ==============================
# LISTA LIVE NOW
# ==============================

@router.get("/now", response_class=HTMLResponse)
def livenow_page(request: Request, db = Depends(get_db)):

        cursor = db.cursor()

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        #current_time = now.strftime("%H:%M")
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
            AND time(ad.StartTime) <= time(?)
            AND time(ad.EndTime)   >= time(?)
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
                "start": r["StartTime"],
                "end": r["EndTime"],                
            })


        return templates.TemplateResponse(
            request,
            "livenow.html",
            {
                "live_items": live_items,
                "now": current_time
            }
        )


@router.get("/status", response_class=HTMLResponse)
def status_page(
        request: Request,
        person: str = Query(default="MAMA"),
        db = Depends(get_db)
    ):

        cursor = db.cursor()

        now = datetime.now()
        iso_day = now.isoweekday()
        current_day = system_day_to_db_day(iso_day)
        current_day_name = now.strftime("%A")
        current_time = now.strftime("%H:%M:%S")

        sql = """
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
        """

        params = [current_day]

        PERSON_LABEL_TO_ID = {
            "TATA": 1,
            "MAMA": 2,
            "GOSIA": 3,
            "EMILKA": 4,
            "RODZINA": 5,
        }

        person = person.upper()
        person_id = PERSON_LABEL_TO_ID.get(person)

        # filtr tylko gdy wybrano konkretną osobę
        if person_id is not None:
            sql += " AND ad.ModelPersonFamilyId = ?"
            params.append(person_id)

        sql += " ORDER BY ad.StartTime"

        rows = cursor.execute(sql, params).fetchall()
        db.close()

        current = None
        next_item = None

        for r in rows:

            item = {
                "start": r["StartTime"],
                "end": r["EndTime"],
                "description": r["Description"],
                "person": r["PersonName"],
                "personPicture": r["PersonPicture"],
                "picture": r["Picture"],
            }

            if r["StartTime"] <= current_time <= r["EndTime"]:
                current = item
            elif r["StartTime"] > current_time and next_item is None:
                next_item = item

        return templates.TemplateResponse(
            request,
            "status.html",
            {                 
                "now": current_time,
                "current": current,
                "next": next_item,
                "current_day_name": current_day_name,

                # 👇 DO WIDOKU
                "selected_person": person_id,
                "persons": list(PERSON_LABEL_TO_ID.keys()),
            }
        )


@router.get("/statusall", response_class=HTMLResponse)
def statusall_page(request: Request, db = Depends(get_db)):

        cursor = db.cursor()

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        iso_day = now.isoweekday()
        current_day = system_day_to_db_day(iso_day)
        current_day_name = now.strftime("%A")

        rows = cursor.execute("""
            SELECT
                ad.Id,
                ad.StartTime,
                ad.EndTime,
                ad.Description,
                pf.Id AS PersonId,
                pf.PersonName,
                pf.PersonPicture,
                pa.Picture,
                pa.Name AS ActivityName
            FROM ActiviesDays ad
            LEFT JOIN PersonFamilies pf
                ON ad.ModelPersonFamilyId = pf.Id
            LEFT JOIN PictureActivities pa
                ON ad.ModelPictureActivityId = pa.Id
            WHERE ad.DayOfWeek = ?
            ORDER BY ad.StartTime
        """, (current_day,)).fetchall()
        
        persons = [
            {"id": 3, "name": "GOSIA"},
            {"id": 2, "name": "MAMA"},
            {"id": 1, "name": "TATA"},
            {"id": 4, "name": "EMILKA"},
            {"id": 5, "name": "ALL"},
        ]

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

        table = {}

        for r in rows:
            
            time_key = f'{hhmm(r["StartTime"])} – {hhmm(r["EndTime"])}'

            if time_key not in table:
                table[time_key] = {p["id"]: None for p in persons}

            person_id = r["PersonId"]   # 🔥 KLUCZOWA LINIA

            if person_id in table[time_key]:
                table[time_key][person_id] = {
                    "activity_id": r["Id"],
                    "description": r["Description"],
                    "picture": r["Picture"],
                    "activityname": r["ActivityName"],
                    "start": r["StartTime"],
                    "end": r["EndTime"],
                    "is_live": r["StartTime"] <= current_time <= r["EndTime"]
                }

        return templates.TemplateResponse(
            request,
            "statusall.html",
            {
                "table": table,
                "persons": persons,
                "day_name": current_day_name,
                "day_index": current_day,   # ✅ TO JEST KLUCZ
                "pictures": pictures,
                "now": current_time,
            }
        )


@router.get("/liveall/{day}", response_class=HTMLResponse)
def statusall_by_day(request: Request, day: int, db = Depends(get_db)):

        cursor = db.cursor()

        # 🔒 zabezpieczenie zakresu
        if day < 1 or day > 7:
            day = system_day_to_db_day(datetime.now().isoweekday())

        current_day = day
        
        #current_day_name = datetime.strptime(str(day)).strftime("%A")
        #current_day_name = current_day.strftime("%A")


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
        current_day_name = DAY_NAMES.get(day, "")


        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        rows = cursor.execute("""
            SELECT
                ad.Id,
                ad.StartTime,
                ad.EndTime,
                ad.Description,
                pf.Id AS PersonId,
                pf.PersonName,
                pf.PersonPicture,
                pa.Picture,
                pa.Name AS ActivityName
            FROM ActiviesDays ad
            LEFT JOIN PersonFamilies pf
                ON ad.ModelPersonFamilyId = pf.Id
            LEFT JOIN PictureActivities pa
                ON ad.ModelPictureActivityId = pa.Id
            WHERE ad.DayOfWeek = ?
            ORDER BY ad.StartTime
        """, (current_day,)).fetchall()

        persons = [
            {"id": 3, "name": "GOSIA"},
            {"id": 2, "name": "MAMA"},
            {"id": 1, "name": "TATA"},
            {"id": 4, "name": "EMILKA"},
            {"id": 5, "name": "ALL"},
        ]

        pictures_raw = cursor.execute("""
            SELECT Id, Name, Picture
            FROM PictureActivities
        """).fetchall()

        pictures = [
            {"id": p["Id"], "label": p["Name"], "picture": p["Picture"]}
            for p in pictures_raw
        ]

        db.close()

        table = {}

        for r in rows:
            time_key = f'{hhmm(r["StartTime"])} – {hhmm(r["EndTime"])}'

            if time_key not in table:
                table[time_key] = {p["id"]: None for p in persons}

            person_id = r["PersonId"]

            if person_id in table[time_key]:
                table[time_key][person_id] = {
                    "activity_id": r["Id"],
                    "description": r["Description"],
                    "picture": r["Picture"],
                    "activityname": r["ActivityName"],
                    "start": r["StartTime"],
                    "end": r["EndTime"],
                    "is_live": r["StartTime"] <= current_time <= r["EndTime"]
                }

        return templates.TemplateResponse(
            request,
            "statusall.html",
            {
                "table": table,
                "persons": persons,
                "day_name": current_day_name,
                "day_index": current_day,   # 🔥 DLA STRZAŁEK
                "pictures": pictures,
                "now": current_time,
            }
        )


@router.get("/statusalltv", response_class=HTMLResponse)
def statusalltv_page(request: Request, db = Depends(get_db)):

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

            time_key = f'{hhmm(r["StartTime"])} – {hhmm(r["EndTime"])}'

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
            request,
            "statusalltv.html",
            {
                "table": table,
                "persons": persons,
                "day_name": current_day_name,
                "now": current_time,
            }
        )

    
@router.put("/statusall/edit/{activity_id}", response_class=HTMLResponse)
def edit_activity_put(
        activity_id: int,
        start: str = Form(...),
        end: str = Form(...),
        description: str = Form(""),
        activityname: str = Form(""),
        db = Depends(get_db)
    ):

        cursor = db.cursor()

        # 🔎 POBIERZ EDYTOWANĄ AKTYWNOŚĆ (ŹRÓDŁO PRAWDY)
        activity = cursor.execute("""
            SELECT
                DayOfWeek,
                ModelPersonFamilyId
            FROM ActiviesDays
            WHERE Id = ?
        """, (activity_id,)).fetchone()

        if not activity:
            db.close()
            raise HTTPException(status_code=404, detail="Aktywność nie istnieje")

        day_of_week = activity["DayOfWeek"]
        person_id = activity["ModelPersonFamilyId"]

        # ===============================
        # 🧠 WALIDACJE PODSTAWOWE
        # ===============================
        start = hhmm(start)
        end = hhmm(end)

        errors = validate_activity_edit_form(
            start,
            end,
            day_of_week,
            person_id
        )

        if errors:
            db.close()
            return JSONResponse(
                {"status": "error", "errors": errors},
                status_code=400
            )

        # ===============================
        # 🔒 KONFLIKT CZASOWY (EDIT)
        # ===============================
        conflict = cursor.execute("""
            SELECT
                StartTime AS start_time,
                EndTime   AS end_time
            FROM ActiviesDays
            WHERE
                DayOfWeek = ?
                AND ModelPersonFamilyId = ?
                AND Id != ?
                AND (
                    time(?) < time(EndTime)
                    AND time(?) > time(StartTime)
                )
            LIMIT 1
        """, (
            day_of_week,
            5 if person_id == 0 else person_id,
            activity_id,
            start,
            end
        )).fetchone()

        if conflict:
            db.close()
            return JSONResponse(
                {
                    "status": "error",
                    "errors": [
                        f"Masz już zaplanowaną aktywność w tym czasie "
                        f"({conflict['start_time']} – {conflict['end_time']})"
                    ]
                },
                status_code=400
            )

        # ===============================
        # 🖼️ AKTYWNOŚĆ → ID OBRAZKA
        # ===============================
        picture_id = None
        if activityname:
            pic = cursor.execute("""
                SELECT Id FROM PictureActivities
                WHERE Name = ?
            """, (activityname,)).fetchone()
            if pic:
                picture_id = pic["Id"]

        # ===============================
        # ✅ UPDATE
        # ===============================
        cursor.execute("""
            UPDATE ActiviesDays
            SET
                StartTime = ?,
                EndTime = ?,
                Description = ?,
                ModelPictureActivityId = ?
            WHERE Id = ?
        """, (
            start,
            end,
            description.strip() or None,
            picture_id,
            activity_id
        ))

        db.commit()
        db.close()

        return JSONResponse({"status": "ok"})

