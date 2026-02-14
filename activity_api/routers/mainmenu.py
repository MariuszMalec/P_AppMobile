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
    prefix="/mainmenu",
    tags=["mainmenu"]
)


# ==============================
# MAIN MENU
# ==============================
@router.get("", response_class=HTMLResponse)    
def mainmenu_page(request: Request, db = Depends(get_db)):

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
            request,
            "mainmenu.html",
            {
                "now": current_time,
                "current": current,
                "next": next_item,
                "current_day_name" : current_day_name,
            }
        ) 

@router.get("home/homebyperson", response_class=HTMLResponse)    
def home_activities_redirect():
        return RedirectResponse("/home/homebyperson", status_code=302)          

