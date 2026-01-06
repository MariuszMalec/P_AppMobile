from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from templates import templates
from enums import ACTIVITY_ENUM_MAP
from validators import (    
    system_day_to_db_day,
)
from db import get_db
from datetime import datetime


def register_routes_pictureactivity(app):

    # ==============================
    # LISTA PICTURE ACTIVITIES
    # ==============================
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
