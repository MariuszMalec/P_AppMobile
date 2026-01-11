from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from starlette.status import HTTP_303_SEE_OTHER
import sqlite3

from templates import templates
from enums import DAY_NAMES, PERSON_ENUM_MAP
from validators import (    
    validate_activity_form,
    validate_activity_edit_form,    
    time_to_minutes,
    normalize_range,
    ranges_overlap,
    hhmm
)
from db import get_db



router = APIRouter(
    prefix="/activities",
    tags=["activities"]
)

@router.get("", response_class=HTMLResponse)
def activities_page(request: Request, db = Depends(get_db)):

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

        # --- OSOBY ---
        p = cursor.execute("""
            SELECT Id, PersonName
            FROM PersonFamilies
        """).fetchall()

        db.close()

        grouped_days = {}

        for r in rows:
            day = r["DayOfWeek"]

            if day not in grouped_days:
                grouped_days[day] = {
                    "dayName": DAY_NAMES.get(day, "Nieznany"),
                    "items": []
                }

            grouped_days[day]["items"].append({
                "id": r["Id"],
                "start": r["StartTime"],
                "end": r["EndTime"],
                "description": r["Description"],
                "person": r["PersonName"],          # ⬅️ gotowe z JOIN
                "personPicture": r["PersonPicture"],
                "picture": r["Picture"],
            })

        return templates.TemplateResponse(
            request,
            "activity.html",
            {
                "days": grouped_days
            }
        )


@router.get("{activity_id}", response_class=JSONResponse)
def get_activity_page(request: Request, activity_id: int, db = Depends(get_db)):

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

        person_id = activity["ModelPersonFamilyId"]
        person = next(
            (p for p in persons_raw if p["Id"] == person_id),
            None
        )
        person_name = person["PersonName"] if person else None

        return JSONResponse({
            "status": "ok",
            "description": activity["Description"],
            "activity_id": f"{activity_id}",
            "person": {
                "id": person["Id"],
                "name": person["PersonName"]
            } if person else None
        })


        
        # return templates.TemplateResponse(
        #     request,
        #     "get_activity.html",
        #     {
        #         "activity": activity,
        #         "persons": persons,
        #         "pictures": pictures,
        #         "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
        #     }
        # )


# ==============================
# DODAWANIE AKTYWNOŚCI
# ==============================
@router.get("/add", response_class=HTMLResponse)
def add_activity_form(request: Request, db = Depends(get_db)):

        cursor = db.cursor()

        cursor.execute("""
            SELECT Id, ActivityName, Name, Picture
            FROM PictureActivities
            ORDER BY Name
        """)
        activities = cursor.fetchall()
        db.close()

        return templates.TemplateResponse(
            request,
            "activity_add.html",
            {
                "persons": PERSON_ENUM_MAP,
                "activities": activities,
                "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
            }
        )


@router.post("/add", response_class=HTMLResponse)
def add_activity_post(
    request: Request,
    start: str = Form(...),
    end: str = Form(...),
    day_of_week: int = Form(...),
    description: str = Form(""),
    person_id: int = Form(...),
    activity_name: str = Form(...),
    db = Depends(get_db),
):
    cursor = db.cursor()

    cursor.execute("SELECT Id, Name FROM PictureActivities ORDER BY Name")
    activities = cursor.fetchall()

    errors, picture_id = validate_activity_form(
        start, end, day_of_week, person_id, activity_name, db
    )

    if errors:
        return templates.TemplateResponse(
            request,
            "activity_add.html",
            {
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
        picture_id
    ))

    db.commit()
    return RedirectResponse("/activities", status_code=303)



# ==============================
# EDYCJA AKTYWNOŚCI
# ==============================
@router.get("/edit/{activity_id}", response_class=HTMLResponse)
def edit_activity_page(request: Request, activity_id: int, db = Depends(get_db)):

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
            person_name = p["PersonName"]
            persons.append({
                "id": p["Id"],
                "label": p["PersonName"]
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
            request,
            "edit_activity.html",
            {
                "activity": activity,
                "persons": persons,
                "pictures": pictures,
                "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
            }
        )


@router.post("/edit/{activity_id}", response_class=HTMLResponse)
def edit_activity_post(
    request: Request,
    activity_id: int,
    day_of_week: int = Form(...),
    start: str = Form(...),
    end: str = Form(...),
    description: str = Form(""),
    person_id: int = Form(...),
    picture_id: int = Form(...),
    db=Depends(get_db)
):
    normalized_person_id = 5 if person_id == 0 else person_id
    errors = validate_activity_edit_form(
        start, end, day_of_week, normalized_person_id
    )

    cursor = db.cursor()

    try:
        # --- pobieramy aktywność ---
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

        # ❌ BŁĘDY FORMULARZA
        if errors:
            return templates.TemplateResponse(
                request,
                "edit_activity.html",
                {
                    "errors": errors,
                    "activity": {
                        "Id": activity_id,
                        "DayOfWeek": day_of_week,
                        "StartTime": start,
                        "EndTime": end,
                        "Description": description,
                        "ModelPersonFamilyId": normalized_person_id,
                        "ModelPictureActivityId": picture_id,
                    },
                    "persons": persons,
                    "pictures": pictures,
                    "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
                },
                status_code=400
            )

        # 🔒 KOLIZJE CZASOWE (bez samej siebie!)
        conflict = cursor.execute("""
            SELECT StartTime, EndTime
            FROM ActiviesDays
            WHERE
                DayOfWeek = ?
                AND ModelPersonFamilyId = ?
                AND Id != ?
                AND time(?) < time(EndTime)
                AND time(?) > time(StartTime)
        """, (
            day_of_week,
            normalized_person_id,
            activity_id,
            start,
            end,
        )).fetchone()

        if conflict:
            return templates.TemplateResponse(
                request,
                "edit_activity.html",
                {
                    "errors": [
                        f"❌ Masz już zaplanowaną aktywność w tym czasie "
                        f"({conflict['StartTime']} – {conflict['EndTime']})"
                    ],
                    "activity": {
                        "Id": activity_id,
                        "DayOfWeek": day_of_week,
                        "StartTime": start,
                        "EndTime": end,
                        "Description": description,
                        "ModelPersonFamilyId": normalized_person_id,
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
            normalized_person_id,
            picture_id,
            activity_id
        ))

        db.commit()
        return RedirectResponse("/activities", status_code=HTTP_303_SEE_OTHER)

    except sqlite3.IntegrityError as e:
        db.rollback()

        if "TIME_OVERLAP" in str(e):
            return templates.TemplateResponse(
                request,
                "edit_activity.html",
                {
                    "errors": ["❌ Masz już zaplanowaną aktywność w tym czasie"],
                    "activity": {
                        "Id": activity_id,
                        "DayOfWeek": day_of_week,
                        "StartTime": start,
                        "EndTime": end,
                        "Description": description,
                        "ModelPersonFamilyId": normalized_person_id,
                        "ModelPictureActivityId": picture_id,
                    },
                    "persons": persons,
                    "pictures": pictures,
                    "days": {k: v for k, v in DAY_NAMES.items() if k != 0},
                },
                status_code=400
            )
        raise

    finally:
        db.close()
             
      

@router.get("/week", response_class=HTMLResponse)
def week_page(request: Request, db = Depends(get_db)):

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

            # 👉 mapowanie osoby
            person_label = None
            if r["PersonName"] is not None:
                enum_value = PERSON_ENUM_MAP.get(r["PersonName"])
                if enum_value:
                    person_label = enum_value.value

            # kopiujemy r i dokładamy nowe pole
            row_dict = dict(r)
            row_dict["PersonName"] = person_label

            week.setdefault(r["DayOfWeek"], []).append(row_dict)


        return templates.TemplateResponse(
            request,
            "week.html",
            {
                "week": week,
                "day_names": DAY_NAMES,   # 👈 KLUCZOWE
            }
        )


@router.post("/delete/{activity_id}")
def delete_activity(activity_id: int, db = Depends(get_db)):

        cur = db.cursor()

        cur.execute(
            "DELETE FROM ActiviesDays WHERE Id = ?",
            (activity_id,)
        )

        db.commit()  # 🔴 to jest kluczowe

        return RedirectResponse("/activities", status_code=303)    