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
            "activities.html",
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

        activities = cursor.execute("""
            SELECT Id, ActivityName, Name, Picture
            FROM PictureActivities
            ORDER BY Name
        """).fetchall()

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

        activities = cursor.execute(
            "SELECT Id, Name FROM PictureActivities ORDER BY Name"
        ).fetchall()

        if errors:
            db.close()
            return templates.TemplateResponse(
                "activity_add.html",
                {
                    "request": request,
                    "errors": errors,
                    "form": locals(),
                    "persons": PERSON_ENUM_MAP,
                    "activities": activities,
                    "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
                },
                status_code=400
            )

        row = cursor.execute(
            "SELECT Id FROM PictureActivities WHERE Name = ?",
            (activity_name,)
        ).fetchone()

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
            5 if person_id == 0 else person_id,
            row["Id"]
        ))

        db.commit()
        db.close()

        return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)


    # ==============================
    # EDYCJA AKTYWNOŚCI
    # ==============================
    @app.get("/activities/edit/{activity_id}", response_class=HTMLResponse)
    def edit_activity_page(request: Request, activity_id: int):
        db = get_db()
        cursor = db.cursor()

        activity = cursor.execute("""
            SELECT *
            FROM ActiviesDays
            WHERE Id = ?
        """, (activity_id,)).fetchone()

        if not activity:
            db.close()
            return HTMLResponse("Nie znaleziono aktywności", status_code=404)

        persons = [
            {
                "id": p["Id"],
                "label": PERSON_ENUM_MAP.get(p["PersonName"], p["PersonName"]).value
            }
            for p in cursor.execute("SELECT * FROM PersonFamilies").fetchall()
        ]

        pictures = cursor.execute("""
            SELECT Id, Name, Picture
            FROM PictureActivities
        """).fetchall()

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
        errors = validate_activity_edit_form(start, end, day_of_week, person_id)

        db = get_db()
        cursor = db.cursor()

        if errors:
            db.close()
            return HTMLResponse(str(errors), status_code=400)

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
 
