from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from templates import templates
from db import get_db


router = APIRouter(
    prefix="/clients",
    tags=["clients"]
)


# =========================================================
# WIDOK KLIENTÓW
# =========================================================

@router.get("/", response_class=HTMLResponse)
def clients_page(
    request: Request,
    db=Depends(get_db)
):
    cursor = db.cursor()

    clients = cursor.execute("""
        SELECT
            Id,
            CreatedAt,
            FirstName,
            LastName,
            Age,
            Description,
            Phone,
            Gender,
            IsActive
        FROM Client
        WHERE IsActive = 1
        ORDER BY FirstName, LastName
    """).fetchall()

    return templates.TemplateResponse(
        "clients.html",
        {
            "request": request,
            "clients": clients
        }
    )


# =========================================================
# LISTA KLIENTÓW JSON
# =========================================================

@router.get("/list")
def get_clients(
    db=Depends(get_db)
):
    cursor = db.cursor()

    clients = cursor.execute("""
        SELECT
            Id,
            CreatedAt,
            FirstName,
            LastName,
            Age,
            Description,
            Phone,
            Gender,
            IsActive
        FROM Client
        WHERE IsActive = 1
        ORDER BY FirstName, LastName
    """).fetchall()

    clients = [dict(client) for client in clients]

    return JSONResponse(content=clients)


# =========================================================
# POBIERANIE JEDNEGO KLIENTA
# =========================================================

@router.get("/{client_id}")
def get_client(
    client_id: int,
    db=Depends(get_db)
):
    cursor = db.cursor()

    client = cursor.execute("""
        SELECT
            Id,
            CreatedAt,
            FirstName,
            LastName,
            Age,
            Description,
            Phone,
            Gender,
            IsActive
        FROM Client
        WHERE Id = ?
    """, (client_id,)).fetchone()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Klient nie istnieje"
        )

    return JSONResponse(
        content=dict(client)
    )


# =========================================================
# CREATE CLIENT
# =========================================================

@router.post("/create")
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

    # -----------------------------------------------------
    # CZYSZCZENIE DANYCH
    # -----------------------------------------------------

    first_name = first_name.strip()
    last_name = last_name.strip()
    description = description.strip()
    phone = phone.strip()
    gender = gender.strip()

    # -----------------------------------------------------
    # PODSTAWOWA WALIDACJA
    # -----------------------------------------------------

    if not first_name:
        raise HTTPException(
            status_code=400,
            detail="Imię jest wymagane"
        )

    if not last_name:
        raise HTTPException(
            status_code=400,
            detail="Nazwisko jest wymagane"
        )

    # -----------------------------------------------------
    # WALIDACJA WIEKU
    # -----------------------------------------------------

    if age is not None and age < 0:
        raise HTTPException(
            status_code=400,
            detail="Wiek nie może być ujemny"
        )

    # -----------------------------------------------------
    # WALIDACJA PŁCI
    # -----------------------------------------------------

    allowed_gender = (
        "male",
        "female",
        "other",
        ""
    )

    if gender not in allowed_gender:
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowa wartość płci"
        )

    # -----------------------------------------------------
    # BLOKADA DUPLIKATU
    # -----------------------------------------------------

    existing = cursor.execute("""
        SELECT Id
        FROM Client
        WHERE LOWER(FirstName) = LOWER(?)
          AND LOWER(LastName) = LOWER(?)
          AND IsActive = 1
    """, (
        first_name,
        last_name
    )).fetchone()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Klient o takim imieniu i nazwisku już istnieje"
        )

    # -----------------------------------------------------
    # DODANIE KLIENTA
    # -----------------------------------------------------

    try:

        cursor.execute("""
            INSERT INTO Client
            (
                FirstName,
                LastName,
                Age,
                Description,
                Phone,
                Gender,
                IsActive
            )
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            first_name,
            last_name,
            age,
            description,
            phone,
            gender
        ))

        client_id = cursor.lastrowid

        db.commit()

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Błąd tworzenia klienta: {str(e)}"
        )

    return JSONResponse({
        "status": "ok",
        "message": "Klient utworzony",
        "client_id": client_id
    })


# =========================================================
# EDIT CLIENT
# =========================================================

@router.put("/edit/{client_id}")
def edit_client(
    client_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    age: int = Form(None),
    description: str = Form(""),
    phone: str = Form(""),
    gender: str = Form(""),
    db=Depends(get_db)
):
    cursor = db.cursor()

    # -----------------------------------------------------
    # POBIERAMY KLIENTA
    # -----------------------------------------------------

    client = cursor.execute("""
        SELECT
            Id,
            FirstName,
            LastName,
            Age,
            Description,
            Phone,
            Gender,
            IsActive
        FROM Client
        WHERE Id = ?
    """, (
        client_id
    )).fetchone()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Klient nie istnieje"
        )

    # -----------------------------------------------------
    # CZYSZCZENIE DANYCH
    # -----------------------------------------------------

    first_name = first_name.strip()
    last_name = last_name.strip()
    description = description.strip()
    phone = phone.strip()
    gender = gender.strip()

    # -----------------------------------------------------
    # WALIDACJA
    # -----------------------------------------------------

    if not first_name:
        raise HTTPException(
            status_code=400,
            detail="Imię jest wymagane"
        )

    if not last_name:
        raise HTTPException(
            status_code=400,
            detail="Nazwisko jest wymagane"
        )

    if age is not None and age < 0:
        raise HTTPException(
            status_code=400,
            detail="Wiek nie może być ujemny"
        )

    allowed_gender = (
        "male",
        "female",
        "other",
        ""
    )

    if gender not in allowed_gender:
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowa wartość płci"
        )

    # -----------------------------------------------------
    # BLOKADA DUPLIKATU
    # -----------------------------------------------------

    existing = cursor.execute("""
        SELECT Id
        FROM Client
        WHERE LOWER(FirstName) = LOWER(?)
          AND LOWER(LastName) = LOWER(?)
          AND Id != ?
          AND IsActive = 1
    """, (
        first_name,
        last_name,
        client_id
    )).fetchone()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Klient o takim imieniu i nazwisku już istnieje"
        )

    # -----------------------------------------------------
    # AKTUALIZACJA
    # -----------------------------------------------------

    try:

        cursor.execute("""
            UPDATE Client
            SET
                FirstName = ?,
                LastName = ?,
                Age = ?,
                Description = ?,
                Phone = ?,
                Gender = ?
            WHERE Id = ?
        """, (
            first_name,
            last_name,
            age,
            description,
            phone,
            gender,
            client_id
        ))

        db.commit()

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Błąd aktualizacji klienta: {str(e)}"
        )

    return JSONResponse({
        "status": "ok",
        "message": "Klient zaktualizowany",
        "client_id": client_id
    })


# =========================================================
# DELETE CLIENT
# =========================================================

@router.delete("/delete/{client_id}")
def delete_client(
    client_id: int,
    db=Depends(get_db)
):
    cursor = db.cursor()

    # -----------------------------------------------------
    # SPRAWDZAMY KLIENTA
    # -----------------------------------------------------

    client = cursor.execute("""
        SELECT
            Id,
            FirstName,
            LastName,
            IsActive
        FROM Client
        WHERE Id = ?
    """, (
        client_id
    )).fetchone()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Klient nie istnieje"
        )

    # -----------------------------------------------------
    # SPRAWDZAMY CZY MA SESJE
    # -----------------------------------------------------

    session_count = cursor.execute("""
        SELECT COUNT(*) AS Count
        FROM Session
        WHERE ClientId = ?
    """, (
        client_id
    )).fetchone()["Count"]

    # -----------------------------------------------------
    # USUWANIE LOGICZNE
    # -----------------------------------------------------

    try:

        cursor.execute("""
            UPDATE Client
            SET IsActive = 0
            WHERE Id = ?
        """, (
            client_id
        ))

        db.commit()

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Błąd usuwania klienta: {str(e)}"
        )

    return JSONResponse({
        "status": "ok",
        "message": "Klient usunięty",
        "client_id": client_id,
        "deleted_sessions": session_count
    })