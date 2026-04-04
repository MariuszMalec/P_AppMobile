from fastapi import APIRouter, Request, Form, Query, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
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
        ORDER BY s.StartTime, s.DayOfWeek
    """).fetchall()

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

    # =========================
    # 🔥 BUDOWANIE TABELI (dni w kolumnach)
    # =========================
    table = {}

    for r in rows:
        time_key = f'{r["StartTime"]} – {r["EndTime"]}'

        if time_key not in table:
            # dla każdego czasu tworzymy wiersz z dniami jako kolumny
            table[time_key] = {day: None for day in range(1, 8)}

        table[time_key][r["DayOfWeek"]] = {
            "session_id": r["Id"],
            "description": f'{r["FirstName"]} {r["LastName"]}',
            "start": r["StartTime"],
            "end": r["EndTime"],
            "is_live": (
                r["DayOfWeek"] == current_day and
                r["StartTime"] <= current_time <= r["EndTime"]
            )
        }

    db.close()

    # =========================
    # 🔥 TEMPLATE RESPONSE
    # =========================
    return templates.TemplateResponse(
        "statusall.html",
        {
            "request": request,
            "table": table,
            "days": days,
            "current_day": current_day,
            "current_time": current_time
        }
    )

# =========================
# EDIT SESSION
# =========================
@router.put("/session/edit/{session_id}")
def edit_session(
    session_id: int,
    start: str = Form(...),
    end: str = Form(...),
    description: str = Form(...),
    db=Depends(get_db)
):
    cursor = db.cursor()

    # Sprawdzenie, czy sesja istnieje
    existing = cursor.execute(
        "SELECT Id FROM Session WHERE Id = ?", (session_id,)
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Sesja nie istnieje")

    # Aktualizacja w bazie
    cursor.execute(
        "UPDATE Session SET StartTime = ?, EndTime = ?, Description = ? WHERE Id = ?",
        (start, end, description, session_id)
    )
    db.commit()
    db.close()

    return JSONResponse({"status": "ok", "message": "Sesja zaktualizowana"})


# =========================
# DELETE SESSION
# =========================
@router.post("/session/delete/{session_id}")
def delete_session(session_id: int, db=Depends(get_db)):
    cursor = db.cursor()

    # Sprawdzenie, czy sesja istnieje
    existing = cursor.execute(
        "SELECT Id FROM Session WHERE Id = ?", (session_id,)
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Sesja nie istnieje")

    # Usuwanie
    cursor.execute("DELETE FROM Session WHERE Id = ?", (session_id,))
    db.commit()
    db.close()

    return JSONResponse({"status": "ok", "message": "Sesja usunięta"})
