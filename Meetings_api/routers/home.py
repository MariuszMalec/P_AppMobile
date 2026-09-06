from fastapi import APIRouter, Request, Form, Query, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi import Query
from starlette.status import HTTP_303_SEE_OTHER
import sqlite3
from templates import templates
from enums import PERSON_ENUM_MAP
from validators import (    
    time_to_minutes,
    ranges_overlap
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
        "statusall.html",
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
    # 2. Walidacja dnia tygodnia
    # ---------------------------------
    if day_of_week < 1 or day_of_week > 7:
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy dzień tygodnia"
        )

    # ---------------------------------
    # 3. Wylicz NOWĄ SessionDate
    #
    # Bierzemy tydzień starej sesji
    # i zmieniamy tylko dzień tygodnia.
    #
    # Python:
    # Monday = 0
    # Sunday = 6
    # ---------------------------------
    try:
        old_date = datetime.strptime(
            old_session_date,
            "%Y-%m-%d"
        ).date()

        monday = old_date - timedelta(
            days=old_date.weekday()
        )

        new_session_date = monday + timedelta(
            days=day_of_week - 1
        )

        new_session_date = new_session_date.isoformat()

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowa data sesji"
        )

    # ---------------------------------
    # 4. Walidacja godzin
    # ---------------------------------
    if not start or not end:
        raise HTTPException(
            status_code=400,
            detail="Godzina rozpoczęcia i zakończenia są wymagane"
        )

    try:
        start_minutes = (
            int(start[:2]) * 60
            + int(start[3:5])
        )

        end_minutes = (
            int(end[:2]) * 60
            + int(end[3:5])
        )

    except (ValueError, IndexError):
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy format godziny"
        )

    if start_minutes >= end_minutes:
        raise HTTPException(
            status_code=400,
            detail="Godzina zakończenia musi być późniejsza niż rozpoczęcia"
        )

    # ---------------------------------
    # 5. Pobierz INNE sesje
    #    z NOWEGO dnia
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
    # 6. Sprawdź konflikt godzin
    # ---------------------------------
    for other in other_sessions:

        other_start = other["StartTime"]
        other_end = other["EndTime"]

        try:
            other_start_minutes = (
                int(other_start[:2]) * 60
                + int(other_start[3:5])
            )

            other_end_minutes = (
                int(other_end[:2]) * 60
                + int(other_end[3:5])
            )

        except (ValueError, IndexError, TypeError):
            continue

        if (
            start_minutes < other_end_minutes
            and end_minutes > other_start_minutes
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Konflikt z sesją {other['Id']} "
                    f"({other_start}-{other_end}) "
                    f"w dniu {new_session_date}"
                )
            )

    # ---------------------------------
    # 7. Aktualizacja
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

    # weryfikacja klienta
    client = cursor.execute(
        "SELECT Id FROM Client WHERE Id = ?",
        (client_id,)
    ).fetchone()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Nie ma takiego klienta"
        )

    # =========================
    # SPRAWDZENIE KONFLIKTU
    # =========================
    other_sessions = cursor.execute(
        """
        SELECT Id, StartTime, EndTime
        FROM Session
        WHERE SessionDate = ?
        ORDER BY StartTime
        """,
        (session_date,)
    ).fetchall()

    try:
        start_minutes = int(start[:2]) * 60 + int(start[3:5])
        end_minutes = int(end[:2]) * 60 + int(end[3:5])
    except (ValueError, IndexError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy format godziny"
        )

    if start_minutes >= end_minutes:
        raise HTTPException(
            status_code=400,
            detail="Godzina zakończenia musi być późniejsza niż rozpoczęcia"
        )

    for other in other_sessions:
        try:
            other_start_minutes = (
                int(other["StartTime"][:2]) * 60
                + int(other["StartTime"][3:5])
            )
            other_end_minutes = (
                int(other["EndTime"][:2]) * 60
                + int(other["EndTime"][3:5])
            )
        except (ValueError, IndexError, TypeError):
            continue

        # konflikt czasowy
        if (
            start_minutes < other_end_minutes
            and end_minutes > other_start_minutes
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Konflikt — sesja już istnieje "
                    f"({other['StartTime']}-{other['EndTime']}) "
                    f"w dniu {session_date}"
                )
            )

    # =========================
    # INSERT
    # =========================
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