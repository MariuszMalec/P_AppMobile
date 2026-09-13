from fastapi import APIRouter, Request, Form, Query, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.status import HTTP_303_SEE_OTHER
import sqlite3
from templates import templates
from enums import PERSON_ENUM_MAP
from validators import (    
    system_day_to_db_day,
)
from db import get_db
from datetime import datetime


router = APIRouter(
    prefix="/home",
    tags=["home"]
)


# ==============================
# HOME
# ==============================
@router.get("", response_class=HTMLResponse)
def home_page(
    request: Request,
    db = Depends(get_db)
):
    cursor = db.cursor()

    try:
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

        current_items = []
        next_items = []

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
                current_items.append(item)
            elif r["StartTime"] > current_time:
                next_items.append(item)

        return templates.TemplateResponse(
            request,
            "home.html",
            {
                "now": current_time,
                "current": current_items,
                "next": next_items,
                "current_day_name": current_day_name,
                "no_data": False,
            },
            status_code=200
        )

    except Exception:
        # brak bazy / tabel / inny błąd → pokaż stronę z komunikatem
        return templates.TemplateResponse(
            request,
            "home.html",
            {
                "now": "",
                "current": [],
                "next": [],
                "current_day_name": "",
                "no_data": True,
            },
            status_code=400
        )

    finally:
        db.close()


@router.get("/homebyperson", response_class=HTMLResponse)    
def home_page_by_person(
        request: Request,
        person: str = Query(default="MAMA"),
        db = Depends(get_db)
    ):

        cursor = db.cursor()

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        iso_day = now.isoweekday()
        current_day = system_day_to_db_day(iso_day)
        current_day_name = now.strftime("%A")

        # ==============================
        # OSOBY Z BAZY
        # ==============================
        person_rows = cursor.execute("""
            SELECT Id, PersonName
            FROM PersonFamilies
            ORDER BY Id
        """).fetchall()

        persons = [
            r["PersonName"]
            for r in person_rows
        ]

        # ==============================
        # MAPA NAZWA -> ID
        # ==============================
        PERSON_STRING_TO_ID = {
            r["PersonName"]: r["Id"]
            for r in person_rows
        }

        # ==============================
        # WYBRANA OSOBA
        # ==============================
        if person in PERSON_STRING_TO_ID:
            selected_person = person
        elif "MAMA" in PERSON_STRING_TO_ID:
            selected_person = "MAMA"
        elif persons:
            selected_person = persons[0]
        else:
            selected_person = ""

        person_id = PERSON_STRING_TO_ID.get(selected_person)

        # ==============================
        # SQL
        # ==============================
        sql = """
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
        """

        params = [current_day]

        # ==============================
        # FILTR OSOBY
        # RODZINA = WSZYSTKIE
        # ==============================
        if selected_person != "RODZINA" and person_id is not None:
            sql += " AND ad.ModelPersonFamilyId = ?"
            params.append(person_id)

        sql += " ORDER BY ad.StartTime"

        rows = cursor.execute(sql, params).fetchall()
        db.close()

        current_items = []
        next_items = []

        for r in rows:
            item = {
                "start": r["StartTime"],
                "end": r["EndTime"],
                "description": r["Description"],
                "person": r["PersonName"],
                "personPicture": r["PersonPicture"],
                "picture": r["Picture"],
            }

            # 🔴 TERAZ
            if r["StartTime"] <= current_time <= r["EndTime"]:
                current_items.append(item)

            # 🔵 NASTĘPNIE
            elif r["StartTime"] > current_time:
                next_items.append(item)

        return templates.TemplateResponse(
            request,
            "statusbyperson.html",
            {
                "now": current_time,
                "current": current_items,
                "next": next_items,
                "current_day_name": current_day_name,
                "persons": persons,
                "selected_person": selected_person,
            }
        )
            
@router.get("/activities", response_class=HTMLResponse)       
def home_activities_redirect():
        return RedirectResponse("/activities", status_code=302)