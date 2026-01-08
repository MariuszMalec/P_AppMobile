from fastapi import APIRouter, Request, Form, Query
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
def home_page(request: Request):
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

        PERSON_NAME_MAP = {
            1: "TATA",
            2: "MAMA",
            3: "GOSIA",
            4: "EMILKA",
            5: "ALL",
        }

        current_items = []
        next_items = []

        for r in rows:
            item = {
                "start": r["StartTime"],
                "end": r["EndTime"],
                "description": r["Description"],
                "person": PERSON_NAME_MAP.get(r["PersonName"], ""),
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
            "home.html",
            {
                "request": request,
                "now": current_time,
                "current": current_items,
                "next": next_items,
                "current_day_name": current_day_name,
            }
        )

@router.get("/homebyperson", response_class=HTMLResponse)    
def home_page_by_person(
        request: Request,
        person: str = Query(default="MAMA")
    ):
        db = get_db()
        cursor = db.cursor()

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        iso_day = now.isoweekday()
        current_day = system_day_to_db_day(iso_day)
        current_day_name = now.strftime("%A")

        # 👉 MAPY (STRING <-> ID)
        PERSON_NAME_MAP = {
            1: "TATA",
            2: "MAMA",
            3: "GOSIA",
            4: "EMILKA",
            5: "ALL",
        }

        PERSON_STRING_TO_ID = {
            "TATA": 1,
            "MAMA": 2,
            "GOSIA": 3,
            "EMILKA": 4,
            "ALL": 5,
        }

        persons = ["ALL", "TATA", "MAMA", "GOSIA", "EMILKA"]
        selected_person = person if person in persons else "ALL"

        person_id = PERSON_STRING_TO_ID[selected_person]

        # 👉 SQL
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

        # 👉 FILTR OSOBY (jeśli nie ALL)
        if person_id != 5:
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
                "person": PERSON_NAME_MAP.get(r["PersonName"], ""),
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
            "statusbyperson.html",
            {
                "request": request,
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

