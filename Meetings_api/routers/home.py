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

    # Poniedziałek danego tygodnia
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
            s.RecurringGroupId,
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
        session_day = datetime.strptime(
            r["SessionDate"],
            "%Y-%m-%d"
        ).isoweekday()

        time_key = f'{r["StartTime"]} – {r["EndTime"]}'

        if time_key not in table:
            table[time_key] = {
                day: None for day in range(1, 8)
            }

        table[time_key][session_day] = {
            "session_id": r["Id"],
            "client_id": r["ClientId"],

            "client": (
                f'{r["FirstName"] or ""} '
                f'{r["LastName"] or ""}'
            ).strip(),

            "description": r["Description"] or "",

            "start": r["StartTime"] or "",
            "end": r["EndTime"] or "",

            "session_date": r["SessionDate"],

            # NULL dla zwykłej sesji
            # ten sam numer dla sesji z jednej serii
            "recurring_group_id": r["RecurringGroupId"],

            "is_recurring": r["RecurringGroupId"] is not None,

            "is_live": (
                r["DayOfWeek"] == current_day
                and r["StartTime"] <= current_time <= r["EndTime"]
            )
        }

    clients = cursor.execute("""
        SELECT Id, FirstName, LastName
        FROM Client
        ORDER BY FirstName, LastName
    """).fetchall()

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
            "week_offset": week_offset,
            "week_start": week_start
        }
    )


@router.get("/session/recurring-count/{recurring_group_id}")
def get_recurring_count(
    recurring_group_id: int,
    db=Depends(get_db)
):
    cursor = db.cursor()

    row = cursor.execute(
        """
        SELECT COUNT(*) AS Count
        FROM Session
        WHERE RecurringGroupId = ?
        """,
        (recurring_group_id,)
    ).fetchone()

    db.close()

    return {
        "count": row["Count"]
    }


@router.put("/session/edit/{session_id}")
def edit_session(
    session_id: int,
    start: str = Form(...),
    end: str = Form(...),
    description: str = Form(""),
    day_of_week: int = Form(...),
    session_date: str = Form(...),
    edit_scope: str = Form("single"),
    recurring_weeks: int = Form(1),
    db=Depends(get_db)
):
    cursor = db.cursor()

    # ---------------------------------------------------------
    # POBIERAMY SESJĘ
    # ---------------------------------------------------------

    session = cursor.execute(
        """
        SELECT
            Id,
            StartTime,
            EndTime,
            DayOfWeek,
            SessionDate,
            ClientId,
            RecurringGroupId
        FROM Session
        WHERE Id = ?
        """,
        (session_id,)
    ).fetchone()

    if not session:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Sesja nie istnieje"
        )

    # ---------------------------------------------------------
    # SPRAWDZAMY ZAKRES EDYCJI
    # ---------------------------------------------------------

    if edit_scope not in ("single", "series"):
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy zakres edycji"
        )

    recurring_group_id = session["RecurringGroupId"]

    if edit_scope == "series" and recurring_group_id is None:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Ta sesja nie należy do serii cyklicznej"
        )

    # ---------------------------------------------------------
    # WALIDACJA DANYCH
    # ---------------------------------------------------------

    try:
        start, end, day_of_week, session_date = validate_session_data(
            start,
            end,
            day_of_week,
            session_date
        )

    except ValueError as e:
        db.close()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # ---------------------------------------------------------
    # WALIDACJA LICZBY TYGODNI
    # ---------------------------------------------------------

    try:
        recurring_weeks = int(recurring_weeks)

    except (TypeError, ValueError):
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowa liczba tygodni"
        )

    if recurring_weeks < 1 or recurring_weeks > 52:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Liczba kolejnych tygodni musi być od 1 do 52"
        )

    # =========================================================
    # EDYCJA POJEDYNCZEJ SESJI
    # =========================================================

    if edit_scope == "single":

        other_sessions = cursor.execute(
            """
            SELECT
                Id,
                StartTime,
                EndTime,
                SessionDate
            FROM Session
            WHERE SessionDate = ?
            ORDER BY StartTime
            """,
            (session_date,)
        ).fetchall()

        conflict = find_time_conflict(
            start,
            end,
            other_sessions,
            exclude_session_id=session_id
        )

        if conflict:
            db.close()

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Konflikt z sesją {conflict['Id']} "
                    f"({conflict['StartTime']}-{conflict['EndTime']}) "
                    f"w dniu {session_date}"
                )
            )

        try:
            cursor.execute(
                """
                UPDATE Session
                SET
                    StartTime = ?,
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
                    session_date,
                    session_id
                )
            )

            db.commit()

        except Exception as e:
            db.rollback()
            db.close()

            raise HTTPException(
                status_code=500,
                detail=f"Błąd aktualizacji sesji: {str(e)}"
            )

        db.close()

        return JSONResponse({
            "status": "ok",
            "message": "Sesja zaktualizowana",
            "session_id": session_id,
            "edit_scope": "single"
        })

    # =========================================================
    # EDYCJA CAŁEJ SERII
    # =========================================================

    series_sessions = cursor.execute(
        """
        SELECT
            Id,
            StartTime,
            EndTime,
            DayOfWeek,
            SessionDate,
            ClientId
        FROM Session
        WHERE RecurringGroupId = ?
        ORDER BY SessionDate
        """,
        (recurring_group_id,)
    ).fetchall()

    if not series_sessions:
        db.close()

        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono sesji serii"
        )

    # ---------------------------------------------------------
    # ILE SESJI MA BYĆ DOCELOWO?
    #
    # 3 kolejne tygodnie = 4 sesje
    # 5 kolejnych tygodni = 6 sesji
    # ---------------------------------------------------------

    target_count = recurring_weeks + 1
    current_count = len(series_sessions)

    # ---------------------------------------------------------
    # PRZESUNIĘCIE DATY SERII
    # ---------------------------------------------------------

    old_date = datetime.strptime(
        session["SessionDate"],
        "%Y-%m-%d"
    ).date()

    new_date = datetime.strptime(
        session_date,
        "%Y-%m-%d"
    ).date()

    date_difference = new_date - old_date

    # ---------------------------------------------------------
    # WYLICZAMY DATY ISTNIEJĄCYCH SESJI
    # ---------------------------------------------------------

    dates_to_update = []

    for series_session in series_sessions:

        old_series_date = datetime.strptime(
            series_session["SessionDate"],
            "%Y-%m-%d"
        ).date()

        new_series_date = (
            old_series_date + date_difference
        ).isoformat()

        dates_to_update.append(
            (
                series_session["Id"],
                new_series_date
            )
        )

    # ---------------------------------------------------------
    # SKRACANIE SERII
    #
    # np. 5 -> 3
    #
    # usuwamy najpóźniejsze sesje
    # ---------------------------------------------------------

    deleted_count = 0

    if target_count < current_count:

        sessions_to_delete = series_sessions[target_count:]

        for series_session in sessions_to_delete:

            cursor.execute(
                """
                DELETE FROM Session
                WHERE Id = ?
                """,
                (series_session["Id"],)
            )

            deleted_count += 1

        series_sessions = series_sessions[:target_count]
        dates_to_update = dates_to_update[:target_count]

    # ---------------------------------------------------------
    # SPRAWDZAMY KONFLIKTY ISTNIEJĄCYCH SESJI
    # ---------------------------------------------------------

    for series_session_id, new_series_date in dates_to_update:

        other_sessions = cursor.execute(
            """
            SELECT
                Id,
                StartTime,
                EndTime,
                SessionDate
            FROM Session
            WHERE SessionDate = ?
              AND RecurringGroupId != ?
            ORDER BY StartTime
            """,
            (
                new_series_date,
                recurring_group_id
            )
        ).fetchall()

        conflict = find_time_conflict(
            start,
            end,
            other_sessions
        )

        if conflict:

            db.rollback()
            db.close()

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Konflikt z sesją {conflict['Id']} "
                    f"({conflict['StartTime']}-{conflict['EndTime']}) "
                    f"w dniu {new_series_date}"
                )
            )

    # ---------------------------------------------------------
    # WYDŁUŻANIE SERII
    #
    # np. 3 -> 5
    #
    # dodajemy brakujące tygodnie
    # ---------------------------------------------------------

    new_dates = []

    if target_count > current_count:

        last_date = datetime.strptime(
            dates_to_update[-1][1],
            "%Y-%m-%d"
        ).date()

        missing_count = target_count - current_count

        for i in range(1, missing_count + 1):

            next_date = (
                last_date +
                timedelta(days=i * 7)
            )

            new_dates.append(next_date)

    # ---------------------------------------------------------
    # SPRAWDZAMY KONFLIKTY NOWYCH SESJI
    # ---------------------------------------------------------

    for new_date_obj in new_dates:

        new_date_str = new_date_obj.isoformat()

        other_sessions = cursor.execute(
            """
            SELECT
                Id,
                StartTime,
                EndTime,
                SessionDate
            FROM Session
            WHERE SessionDate = ?
            ORDER BY StartTime
            """,
            (new_date_str,)
        ).fetchall()

        conflict = find_time_conflict(
            start,
            end,
            other_sessions
        )

        if conflict:

            db.rollback()
            db.close()

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Konflikt z sesją {conflict['Id']} "
                    f"({conflict['StartTime']}-{conflict['EndTime']}) "
                    f"w dniu {new_date_str}"
                )
            )

    # ---------------------------------------------------------
    # ZAPISUJEMY ZMIANY
    # ---------------------------------------------------------

    created_count = 0

    try:

        # Aktualizacja istniejących sesji
        for series_session_id, new_series_date in dates_to_update:

            cursor.execute(
                """
                UPDATE Session
                SET
                    StartTime = ?,
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
                    new_series_date,
                    series_session_id
                )
            )

        # Dodawanie nowych sesji
        for new_date_obj in new_dates:

            cursor.execute(
                """
                INSERT INTO Session (
                    StartTime,
                    EndTime,
                    ClientId,
                    Description,
                    DayOfWeek,
                    SessionDate,
                    RecurringGroupId
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    start,
                    end,
                    session["ClientId"],
                    description,
                    day_of_week,
                    new_date_obj.isoformat(),
                    recurring_group_id
                )
            )

            created_count += 1

        db.commit()

    except Exception as e:

        db.rollback()
        db.close()

        raise HTTPException(
            status_code=500,
            detail=f"Błąd aktualizacji serii: {str(e)}"
        )

    db.close()

    return JSONResponse({
        "status": "ok",
        "message": "Cała seria została zaktualizowana",
        "session_id": session_id,
        "recurring_group_id": recurring_group_id,
        "edit_scope": "series",
        "recurring_weeks": recurring_weeks,
        "total_count": target_count,
        "created_count": created_count,
        "deleted_count": deleted_count
    })


# =========================
# DELETE SESSION
# =========================
@router.post("/session/delete/{session_id}")
def delete_session(
    session_id: int,
    delete_scope: str = Form("single"),
    db=Depends(get_db)
):
    cursor = db.cursor()

    session = cursor.execute(
        """
        SELECT
            Id,
            RecurringGroupId
        FROM Session
        WHERE Id = ?
        """,
        (session_id,)
    ).fetchone()

    if not session:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Sesja nie istnieje"
        )

    if delete_scope not in ("single", "series"):
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy zakres usuwania"
        )

    recurring_group_id = session["RecurringGroupId"]

    if delete_scope == "series" and recurring_group_id is None:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Ta sesja nie należy do serii cyklicznej"
        )

    try:

        if delete_scope == "single":

            cursor.execute(
                """
                DELETE FROM Session
                WHERE Id = ?
                """,
                (session_id,)
            )

            deleted_count = cursor.rowcount

        else:

            cursor.execute(
                """
                DELETE FROM Session
                WHERE RecurringGroupId = ?
                """,
                (recurring_group_id,)
            )

            deleted_count = cursor.rowcount

        db.commit()

    except Exception as e:

        db.rollback()
        db.close()

        raise HTTPException(
            status_code=500,
            detail=f"Błąd usuwania sesji: {str(e)}"
        )

    db.close()

    return JSONResponse({
        "status": "ok",
        "message": (
            "Sesja usunięta"
            if delete_scope == "single"
            else "Cała seria została usunięta"
        ),
        "deleted_count": deleted_count,
        "delete_scope": delete_scope,
        "recurring_group_id": recurring_group_id
    })

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
    recurring: str = Form("false"),
    recurring_weeks: int = Form(1),
    db=Depends(get_db)
):
    cursor = db.cursor()

    # ---------------------------------
    # 1. Walidacja danych podstawowych
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
        db.close()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # ---------------------------------
    # 2. Sprawdzenie cykliczności
    # ---------------------------------
    recurring_bool = str(recurring).lower() in (
        "true",
        "1",
        "yes",
        "on"
    )

    try:
        recurring_weeks = int(recurring_weeks)
    except (TypeError, ValueError):
        db.close()

        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowa liczba tygodni cykliczności"
        )

    if recurring_bool:

        if recurring_weeks < 1 or recurring_weeks > 52:
            db.close()

            raise HTTPException(
                status_code=400,
                detail="Liczba kolejnych tygodni musi być od 1 do 52"
            )

    else:
        recurring_weeks = 0

    # ---------------------------------
    # 3. Sprawdzenie klienta
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
        db.close()

        raise HTTPException(
            status_code=404,
            detail="Nie ma takiego klienta"
        )

    # ---------------------------------
    # 4. Przygotowanie dat
    # ---------------------------------
    try:
        base_date = datetime.strptime(
            session_date,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        db.close()

        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy format session_date"
        )

    dates = [base_date]

    if recurring_bool:

        for week in range(1, recurring_weeks + 1):

            dates.append(
                base_date + timedelta(days=week * 7)
            )

    # ---------------------------------
    # 5. Sprawdzenie konfliktów
    #    dla wszystkich dat
    # ---------------------------------
    conflicts = []

    for current_date in dates:

        current_date_str = current_date.strftime(
            "%Y-%m-%d"
        )

        other_sessions = cursor.execute(
            """
            SELECT
                Id,
                StartTime,
                EndTime
            FROM Session
            WHERE SessionDate = ?
            ORDER BY StartTime
            """,
            (current_date_str,)
        ).fetchall()

        conflict = find_time_conflict(
            start,
            end,
            other_sessions
        )

        if conflict:

            conflicts.append(
                {
                    "date": current_date_str,
                    "start": conflict["StartTime"],
                    "end": conflict["EndTime"]
                }
            )

    # ---------------------------------
    # 6. Jeżeli jest konflikt,
    #    nie tworzymy nic
    # ---------------------------------
    if conflicts:

        conflict_messages = []

        for conflict in conflicts:

            conflict_messages.append(
                f"{conflict['date']}: "
                f"{conflict['start']}-{conflict['end']}"
            )

        db.close()

        raise HTTPException(
            status_code=400,
            detail=(
                "Nie można utworzyć serii sesji. "
                "Wykryto konflikt:\n"
                + "\n".join(conflict_messages)
            )
        )

    # ---------------------------------
    # 7. TWORZENIE SESJI
    # ---------------------------------
    try:

        recurring_group_id = None

        # =================================
        # ZWYKŁA SESJA
        # =================================
        if not recurring_bool:

            cursor.execute(
                """
                INSERT INTO Session (
                    StartTime,
                    EndTime,
                    ClientId,
                    Description,
                    DayOfWeek,
                    SessionDate,
                    RecurringGroupId
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    start,
                    end,
                    client_id,
                    description,
                    day_of_week,
                    base_date.strftime("%Y-%m-%d")
                )
            )

        # =================================
        # SESJA CYKLICZNA
        # =================================
        else:

            # ---------------------------------
            # Pierwsza sesja
            # ---------------------------------
            cursor.execute(
                """
                INSERT INTO Session (
                    StartTime,
                    EndTime,
                    ClientId,
                    Description,
                    DayOfWeek,
                    SessionDate,
                    RecurringGroupId
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    start,
                    end,
                    client_id,
                    description,
                    day_of_week,
                    dates[0].strftime("%Y-%m-%d")
                )
            )

            # Id pierwszej sesji staje się
            # identyfikatorem całej serii
            recurring_group_id = cursor.lastrowid

            # ---------------------------------
            # Przypisz grupę pierwszej sesji
            # ---------------------------------
            cursor.execute(
                """
                UPDATE Session
                SET RecurringGroupId = ?
                WHERE Id = ?
                """,
                (
                    recurring_group_id,
                    recurring_group_id
                )
            )

            # ---------------------------------
            # Pozostałe sesje serii
            # ---------------------------------
            for current_date in dates[1:]:

                cursor.execute(
                    """
                    INSERT INTO Session (
                        StartTime,
                        EndTime,
                        ClientId,
                        Description,
                        DayOfWeek,
                        SessionDate,
                        RecurringGroupId
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        start,
                        end,
                        client_id,
                        description,
                        day_of_week,
                        current_date.strftime("%Y-%m-%d"),
                        recurring_group_id
                    )
                )

        # ---------------------------------
        # 8. Zapisujemy wszystko
        # ---------------------------------
        db.commit()

    except Exception as e:

        db.rollback()

        db.close()

        raise HTTPException(
            status_code=500,
            detail=f"Błąd tworzenia sesji: {str(e)}"
        )

    finally:

        try:
            db.close()
        except:
            pass

    # ---------------------------------
    # 9. Odpowiedź
    # ---------------------------------
    return JSONResponse({
        "status": "ok",
        "message": (
            f"Utworzono {len(dates)} "
            f"{'sesji cyklicznych' if recurring_bool else 'sesję'}"
        ),
        "created": len(dates),
        "recurring_group_id": recurring_group_id,
        "dates": [
            d.strftime("%Y-%m-%d")
            for d in dates
        ]
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