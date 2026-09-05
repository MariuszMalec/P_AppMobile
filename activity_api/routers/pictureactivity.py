from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from templates import templates
from enums import ACTIVITY_ENUM_MAP
from validators import (    
    system_day_to_db_day,
)
from db import get_db
from datetime import datetime

router = APIRouter(
    prefix="/pictureactivities",
    tags=["pictureactivities"]
)


# ==============================
# LISTA PICTURE ACTIVITIES
# ==============================

@router.get("", response_class=HTMLResponse)
def picture_activities_page(request: Request, db = Depends(get_db)):

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
            request,
            "pictureactivities.html",
            {
                "items": items
            }
        )


    # ---------- EDIT PICTURE ACTIVITY ----------
    
    
@router.get("/edit/{item_id}", response_class=HTMLResponse)
def edit_picture_activity_form(item_id: int, request: Request, db = Depends(get_db)):

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
            request,
            "pictureactivity_edit.html",
            {
                "item": {
                    "id": row["Id"],
                    "name": row["Name"],          # ✅ STRING
                    "picture": row["Picture"]
                },
                "activities": ACTIVITY_ENUM_MAP  # tylko do listy opcji
            }
        )


@router.post("/edit/{item_id}", response_class=HTMLResponse)
def edit_picture_activity_save(
        item_id: int,
        name: str = Form(...),      # ✅ STRING
        picture: str = Form(""), 
        db = Depends(get_db)
        
    ):

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

    # ---------- ADD PICTURE ACTIVITY ----------
    
    
@router.get("/add", response_class=HTMLResponse)
def add_picture_activity_form(request: Request, db = Depends(get_db)):
        return templates.TemplateResponse(
            request,
            "pictureactivity_add.html",
            {
                "activities": ACTIVITY_ENUM_MAP
            }
        )

@router.post("/add", response_class=HTMLResponse)
def add_picture_activity_save(
        request: Request,
        activityName: int = Form(...),
        name: str = Form(...),
        picture: str = Form(""),
        db = Depends(get_db)
    ):
    errors = []

    name = name.strip()
    picture = picture.strip()

    # -------------------------
    # WALIDACJA NAME
    # -------------------------

    if not name:
        errors.append("Nazwa jest wymagana")

    elif len(name) > 15:
        errors.append("Nazwa może mieć maksymalnie 15 znaków")

    # -------------------------
    # JEŚLI SĄ BŁĘDY
    # -------------------------

    if errors:
        return templates.TemplateResponse(
            request,
            "pictureactivity_add.html",
            {
                "activities": ACTIVITY_ENUM_MAP,
                "errors": errors,
                "form": {
                    "activityName": activityName,
                    "name": name,
                    "picture": picture,
                }
            }
        )

    cursor = db.cursor()

    # -------------------------
    # SPRAWDZENIE CZY NAME JUŻ ISTNIEJE
    # -------------------------

    cursor.execute("""
        SELECT Id
        FROM PictureActivities
        WHERE Name = ?
        LIMIT 1
    """, (name,))

    if cursor.fetchone():
        db.close()

        return templates.TemplateResponse(
            request,
            "pictureactivity_add.html",
            {
                "activities": ACTIVITY_ENUM_MAP,
                "errors": [
                    "Taka nazwa aktywności już istnieje"
                ],
                "form": {
                    "activityName": activityName,
                    "name": name,
                    "picture": picture,
                }
            }
        )

    # -------------------------
    # OBSŁUGA "INNE"
    # -------------------------

    # Szukamy ID pozycji "Inne" w ACTIVITY_ENUM_MAP
    other_activity_id = next(
        (
            k for k, v in ACTIVITY_ENUM_MAP.items()
            if str(v.value).strip().lower() == "inne"
        ),
        None
    )

    # Jeżeli wybrano "Inne" -> nadajemy kolejne ID
    if other_activity_id is not None and activityName == other_activity_id:

        cursor.execute("""
            SELECT COALESCE(MAX(ActivityName), 0) + 1
            FROM PictureActivities
        """)

        activityName = cursor.fetchone()[0]

    # -------------------------
    # ZAPIS
    # -------------------------

    try:
        cursor.execute("""
            INSERT INTO PictureActivities
                (ActivityName, Name, Picture)
            VALUES (?, ?, ?)
        """, (
            activityName,
            name,
            picture or None
        ))

        db.commit()

    except sqlite3.IntegrityError:
        db.close()

        return templates.TemplateResponse(
            request,
            "pictureactivity_add.html",
            {
                "activities": ACTIVITY_ENUM_MAP,
                "errors": [
                    "Ta aktywność MA JUŻ przypisany obrazek"
                ],
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
