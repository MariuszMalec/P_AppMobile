from fastapi import Request
from fastapi.responses import HTMLResponse
import sqlite3
from db import DB_PATH
from templates import templates
from enums import DAY_NAMES, PERSON_ENUM_MAP
from validators import (    
    system_day_to_db_day,
    hhmm
)
from db import get_db
from datetime import datetime


def register_routes_livenow(app):

    # ==============================
    # LISTA LIVE NOW
    # ==============================
    @app.get("/livenow", response_class=HTMLResponse)
    def livenow_page(request: Request):
        db = get_db()
        cursor = db.cursor()

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
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
            AND ad.StartTime <= ?
            AND ad.EndTime >= ?
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
            "livenow.html",
            {
                "request": request,
                "live_items": live_items,
                "now": current_time
            }
        )


    @app.get("/status", response_class=HTMLResponse)
    def status_page(request: Request):
        db = get_db()
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
            "home.html",
            {
                "request": request,
                "now": current_time,
                "current": current,
                "next": next_item,
                "current_day_name" : current_day_name,
            }
        )



    @app.get("/statusall", response_class=HTMLResponse)
    def statusall_page(request: Request):
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
            time_key = f'{r["StartTime"]} – {r["EndTime"]}'

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
            "statusall.html",
            {
                "request": request,
                "table": table,
                "persons": persons,
                "day_name": current_day_name,
                "now": current_time,
            }
        )


    @app.get("/statusalltv", response_class=HTMLResponse)
    def statusalltv_page(request: Request):
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
            {"id": 0, "name": "ALL"},
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
            "statusalltv.html",
            {
                "request": request,
                "table": table,
                "persons": persons,
                "day_name": current_day_name,
                "now": current_time,
            }
        )



