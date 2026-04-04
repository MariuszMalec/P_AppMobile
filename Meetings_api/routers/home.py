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
@router.get("/", response_class=HTMLResponse)
def home_page(request: Request, db=Depends(get_db)):

    cursor = db.cursor()

    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_day = now.isoweekday()

    # 🔥 POBIERAMY CAŁY TYDZIEŃ
    rows = cursor.execute("""
        SELECT
            s.Id,
            s.StartTime,
            s.EndTime,
            s.Description,
            s.DayOfWeek,
            c.Id AS ClientId,
            c.FirstName,
            c.LastName
        FROM Session s
        LEFT JOIN Client c
            ON s.ClientId = c.Id
        ORDER BY s.DayOfWeek, s.StartTime
    """).fetchall()

    # 👇 klienci (kolumny)
    clients_raw = cursor.execute("""
        SELECT Id, FirstName, LastName
        FROM Client
        WHERE IsActive = 1
    """).fetchall()

    clients = [
        {
            "id": c["Id"],
            "name": f'{c["FirstName"]} {c["LastName"]}'
        }
        for c in clients_raw
    ]

    # 👇 dni tygodnia
    days = {
        1: "Poniedziałek",
        2: "Wtorek",
        3: "Środa",
        4: "Czwartek",
        5: "Piątek",
        6: "Sobota",
        7: "Niedziela"
    }

    db.close()

    # =========================
    # 🔥 BUDOWANIE TABELI
    # =========================
    table = {}

    for r in rows:

        day = r["DayOfWeek"]
        time_key = f'{r["StartTime"]} – {r["EndTime"]}'

        if day not in table:
            table[day] = {}

        if time_key not in table[day]:
            table[day][time_key] = {c["id"]: None for c in clients}

        client_id = r["ClientId"]

        if client_id in table[day][time_key]:
            table[day][time_key][client_id] = {
                "session_id": r["Id"],
                "description": r["Description"],
                "start": r["StartTime"],
                "end": r["EndTime"],
                "is_live": (
                    day == current_day and
                    r["StartTime"] <= current_time <= r["EndTime"]
                )
            }

    # =========================
    # 🔥 TEMPLATE RESPONSE
    # =========================
    return templates.TemplateResponse(
        "statusall.html",
        {
            "request": request,   # 🔥 MUSI BYĆ
            "table": table,       # tabela z sesjami
            "clients": clients,   # lista klientów
            "days": days,         # dni tygodnia
            "current_day": current_day,
            "current_time": current_time
        }
    )