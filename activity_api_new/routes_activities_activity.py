from fastapi import Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.status import HTTP_303_SEE_OTHER
import sqlite3
from db import DB_PATH
from templates import templates
from enums import DAY_NAMES, PERSON_ENUM_MAP
from validators import (    
    validate_activity_form,
    validate_activity_edit_form,    
)
from db import get_db


def register_routes_activity(app):

    # ==============================
    # LISTA AKTYWNOŚCI
    # ==============================
    @app.get("/activity", response_class=HTMLResponse)
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

            person_label = None
            if r["PersonName"] is not None:
                enum_value = PERSON_ENUM_MAP.get(r["PersonName"])
                if enum_value:
                    person_label = enum_value.value

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
            "activity.html",
            {
                "request": request,
                "days": grouped_days
            }
        )


    # ==============================
    # DODAWANIE AKTYWNOŚCI
    # ==============================
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

        # 🔒 BLOKADA: ta sama osoba + ten sam dzień + zachodzący przedział czasu
        cursor.execute("""
            SELECT
                StartTime AS start_time,
                EndTime   AS end_time
            FROM ActiviesDays
            WHERE
                DayOfWeek = ?
                AND ModelPersonFamilyId = ?
                AND (
                    time(?) < time(EndTime)
                    AND time(?) > time(StartTime)
                )
            LIMIT 1 
        """, (
            day_of_week,
            5 if person_id == 0 else person_id,
            start,   # INT (sekundy)
            end      # INT (sekundy)
        ))       

        conflict = cursor.fetchone()

        if conflict:
            db.close()
            return templates.TemplateResponse(
                "activity_add.html",
                {
                    "request": request,
                    "errors": [ 
                        f"❌ Masz już zaplanowaną aktywność w tym czasie "
                        f"({conflict['start_time']} – {conflict['end_time']})"
                    ],
                    "form": {
                        "start": start,
                        "end": end,
                        "day_of_week": day_of_week,
                        "description": description,
                        "person_id": person_id,
                        "activity_name": activity_name,
                    },
                    "persons": PERSON_ENUM_MAP,
                    "activities": activities,
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
        try:
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
                5 if person_id == 0 else person_id,  # ✅ # 0 = ALL → zapisujemy jako RODZINA (Id=5)
                picture_id
            ))

            db.commit()
            db.close()
        except sqlite3.IntegrityError as e:
            db.rollback()

            if "TIME_OVERLAP" in str(e):
                db.close()
                return templates.TemplateResponse(
                    "activity_add.html",
                    {
                        "request": request,
                        "errors": [
                            "❌ Masz już zaplanowaną aktywność w tym czasie (TIME_OVERLAP)"
                        ],
                        "form": {
                            "start": start,
                            "end": end,
                            "day_of_week": day_of_week,
                            "description": description,
                            "person_id": person_id,
                            "activity_name": activity_name,
                        },
                        "persons": PERSON_ENUM_MAP,
                        "activities": activities,
                        "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
                    },
                    status_code=400
                )          

        return RedirectResponse("/activity", status_code=303)


    # ==============================
    # EDYCJA AKTYWNOŚCI
    # ==============================
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
        
        # 🔒 BLOKADA: konflikt czasu (EDIT) – pomijamy edytowaną aktywność
        cursor.execute("""
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
        ))

        conflict = cursor.fetchone()

        if conflict:
            db.close()
            return templates.TemplateResponse(
                "edit_activity.html",
                {
                    "request": request,
                    "errors": [
                        f"❌ Masz już zaplanowaną aktywność w tym czasie "
                        f"({conflict['start_time']} – {conflict['end_time']})"
                    ],
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

        return RedirectResponse("/activity", status_code=HTTP_303_SEE_OTHER)
    

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

        return RedirectResponse("/activity", status_code=303)    