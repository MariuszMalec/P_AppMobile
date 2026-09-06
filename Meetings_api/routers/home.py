from fastapi import APIRouter, Request, Form, Query, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi import Query
from starlette.status import HTTP_303_SEE_OTHER
import sqlite3
from templates import templates

from validators import (
    validate_session_data,
    find_time_conflict,
    validate_client_id,
    validate_client_data
)

from db import get_db
from datetime import datetime


router = APIRouter(
    prefix="/home",
    tags=["home"]
)



from datetime import datetime, timedelta

@router.get("/", response_class=HTMLResponse)
def home_page(
    request: Request,
    db=Depends(get_db),
    week_offset: int = Query(0)
):

    cursor = db.cursor()

    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_day = now.isoweekday()

    # Wylicz datę poniedziałku tygodnia z uwzględnieniem przesunięcia
    monday = now - timedelta(days=now.weekday()) + timedelta(weeks=week_offset)
    sunday = monday + timedelta(days=6)
    week_start = monday.date().isoformat()
    week_end = sunday.date().isoformat()

    # POBIERAMY SESJE Z DANEGO TYGODNIA
    rows = cursor.execute("""
        SELECT
            s.Id,
            s.StartTime,
            s.EndTime,
            s.Description,
            s.DayOfWeek,
            s.SessionDate,
            c.Id AS ClientId,
            c.FirstName,
            c.LastName
        FROM Session s
        LEFT JOIN Client c
            ON s.ClientId = c.Id
        WHERE s.SessionDate BETWEEN ? AND ?
        ORDER BY s.StartTime, s.DayOfWeek
    """, (week_start, week_end)).fetchall()

    days = {
        1: "Poniedziałek",
        2: "Wtorek",
        3: "Środa",
        4: "Czwartek",
        5: "Piątek",
        6: "Sobota",
        7: "Niedziela"
    }

    table = {}

    for r in rows:
        time_key = f'{r["StartTime"]} – {r["EndTime"]}'

        if time_key not in table:
            table[time_key] = {day: None for day in range(1, 8)}

        table[time_key][r["DayOfWeek"]] = {
            "session_id": r["Id"],
            "client": f'{r["FirstName"] or ""} {r["LastName"] or ""}'.strip(),
            "description": r["Description"] or "",
            "start": r["StartTime"] or "",
            "end": r["EndTime"] or "",
            "session_date": r["SessionDate"],        # <-- dodaj to
            "is_live": (
                r["DayOfWeek"] == current_day and
                r["StartTime"] <= current_time <= r["EndTime"]
            )
        }

    
    clients = cursor.execute("SELECT Id, FirstName, LastName FROM Client ORDER BY FirstName, LastName").fetchall()

    db.close()

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "table": table,
            "days": days,
            "current_day": current_day,
            "current_time": current_time,
            "clients": clients,
            "week_offset": week_offset,   # ✔️ TUTAJ
            "week_start": week_start      # (opcjonalnie ale potrzebne)
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
    day_of_week: int = Form(...),
    db=Depends(get_db)
):
    cursor = db.cursor()

    # ---------------------------------
    # 1. Pobierz edytowaną sesję
    # ---------------------------------
    session = cursor.execute(
        """
        SELECT Id, StartTime, EndTime, DayOfWeek, SessionDate
        FROM Session
        WHERE Id = ?
        """,
        (session_id,)
    ).fetchone()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Sesja nie istnieje"
        )

    old_session_date = session["SessionDate"]

    # ---------------------------------
    # 2. Wylicz nową SessionDate
    #
    # Bierzemy tydzień starej sesji
    # i zmieniamy tylko dzień tygodnia.
    # ---------------------------------
    try:
        old_date = datetime.strptime(
            old_session_date,
            "%Y-%m-%d"
        ).date()

        monday = old_date - timedelta(
            days=old_date.weekday()
        )

        new_session_date = (
            monday + timedelta(days=day_of_week - 1)
        ).isoformat()

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowa data sesji"
        )

    # ---------------------------------
    # 3. Walidacja danych
    # ---------------------------------
    try:
        start, end, day_of_week, new_session_date = validate_session_data(
            start,
            end,
            day_of_week,
            new_session_date
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # ---------------------------------
    # 4. Pobierz inne sesje z nowego dnia
    # ---------------------------------
    other_sessions = cursor.execute(
        """
        SELECT Id, StartTime, EndTime, SessionDate
        FROM Session
        WHERE SessionDate = ?
          AND Id != ?
        ORDER BY StartTime
        """,
        (
            new_session_date,
            session_id
        )
    ).fetchall()

    # ---------------------------------
    # 5. Sprawdź konflikt czasowy
    # ---------------------------------
    conflict = find_time_conflict(
        start,
        end,
        other_sessions
    )

    if conflict:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Konflikt z sesją {conflict['Id']} "
                f"({conflict['StartTime']}-{conflict['EndTime']}) "
                f"w dniu {new_session_date}"
            )
        )

    # ---------------------------------
    # 6. Aktualizacja
    # ---------------------------------
    cursor.execute(
        """
        UPDATE Session
        SET StartTime = ?,
            EndTime = ?,
            Description = ?,
            DayOfWeek = ?,
            SessionDate = ?
        WHERE Id = ?
        """,
        (
            start,
            end,
            description,
            day_of_week,
            new_session_date,
            session_id
        )
    )

    db.commit()
    db.close()

    return JSONResponse({
        "status": "ok",
        "message": "Sesja zaktualizowana"
    })

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


# =========================
# CREATE SESSION
# =========================
@router.post("/session/create")
def create_session(
    start: str = Form(...),
    end: str = Form(...),
    client_id: int = Form(...),
    description: str = Form(""),
    day_of_week: int = Form(...),
    session_date: str = Form(...),
    db=Depends(get_db)
):
    cursor = db.cursor()

    # ---------------------------------
    # 1. Walidacja danych sesji
    # ---------------------------------
    try:
        start, end, day_of_week, session_date = validate_session_data(
            start,
            end,
            day_of_week,
            session_date
        )

        client_id = validate_client_id(client_id)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # ---------------------------------
    # 2. Sprawdzenie klienta
    # ---------------------------------
    client = cursor.execute(
        """
        SELECT Id
        FROM Client
        WHERE Id = ?
        """,
        (client_id,)
    ).fetchone()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Nie ma takiego klienta"
        )

    # ---------------------------------
    # 3. Pobierz sesje z tego dnia
    # ---------------------------------
    other_sessions = cursor.execute(
        """
        SELECT Id, StartTime, EndTime
        FROM Session
        WHERE SessionDate = ?
        ORDER BY StartTime
        """,
        (session_date,)
    ).fetchall()

    # ---------------------------------
    # 4. Sprawdzenie konfliktu
    # ---------------------------------
    conflict = find_time_conflict(
        start,
        end,
        other_sessions
    )

    if conflict:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Konflikt — sesja już istnieje "
                f"({conflict['StartTime']}-{conflict['EndTime']}) "
                f"w dniu {session_date}"
            )
        )

    # ---------------------------------
    # 5. INSERT
    # ---------------------------------
    cursor.execute(
        """
        INSERT INTO Session (
            StartTime,
            EndTime,
            ClientId,
            Description,
            DayOfWeek,
            SessionDate
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            start,
            end,
            client_id,
            description,
            day_of_week,
            session_date
        )
    )

    db.commit()
    db.close()

    return JSONResponse({
        "status": "ok",
        "message": "Sesja utworzona"
    })


@router.get("/get_clients")
def get_clients(db=Depends(get_db)):
    cursor = db.cursor()

    # Pobieranie wszystkich klientów
    clients = cursor.execute("SELECT Id, FirstName, LastName FROM Client ORDER BY FirstName, LastName").fetchall()

    clients = [dict(client) for client in clients]

    return JSONResponse(content=clients)


# =========================
# CREATE CLIENT
# =========================
@router.post("/client/create")
def create_client(
    first_name: str = Form(...),
    last_name: str = Form(...),
    age: int = Form(None),
    description: str = Form(""),
    phone: str = Form(""),
    gender: str = Form(""),
    db=Depends(get_db)
):
    cursor = db.cursor()

    first_name = first_name.strip()
    last_name = last_name.strip()

    if not first_name or not last_name:
        raise HTTPException(status_code=400, detail="Imię i nazwisko są wymagane")

    # 🔒 BLOKADA DUPLIKATU
    existing = cursor.execute("""
        SELECT Id FROM Client
        WHERE LOWER(FirstName) = LOWER(?) 
          AND LOWER(LastName) = LOWER(?)
    """, (first_name, last_name)).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Klient już istnieje")

    cursor.execute("""
        INSERT INTO Client (FirstName, LastName, Age, Description, Phone, Gender)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (first_name, last_name, age, description, phone, gender))

    db.commit()
    db.close()

    return JSONResponse({
        "status": "ok",
        "message": "Klient utworzony"
    })