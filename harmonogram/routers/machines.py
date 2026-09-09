from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import HTMLResponse
from templates import templates
from db import get_db

router = APIRouter(
    prefix="/machines",
    tags=["machines"]
)


# =====================================================
# LISTA MASZYN
# =====================================================
@router.get("", response_class=HTMLResponse)
def machines_page(request: Request, db=Depends(get_db)):
    cursor = db.cursor()

    machines = cursor.execute("""
        SELECT Id, Name, Description, Picture
        FROM Machines
        ORDER BY Id
    """).fetchall()

    return templates.TemplateResponse(
        "machines.html",
        {
            "request": request,
            "machines": machines
        }
    )


# =====================================================
# POBRANIE JEDNEJ MASZYNY
# =====================================================
@router.get("/{machine_id}")
def get_machine(machine_id: int, db=Depends(get_db)):
    cursor = db.cursor()

    machine = cursor.execute("""
        SELECT Id, Name, Description, Picture
        FROM Machines
        WHERE Id = ?
    """, (machine_id,)).fetchone()

    if not machine:
        return {
            "status": "error",
            "message": "Maszyna nie istnieje!"
        }

    return {
        "status": "ok",
        "machine": dict(machine)
    }


# =====================================================
# EDYCJA MASZYNY
# =====================================================
@router.post("/edit/{machine_id}")
def edit_machine(
    machine_id: int,
    data: dict = Body(...),
    db=Depends(get_db)
):
    cursor = db.cursor()

    existing = cursor.execute("""
        SELECT 1
        FROM Machines
        WHERE Id = ?
    """, (machine_id,)).fetchone()

    if not existing:
        return {
            "status": "error",
            "message": "Maszyna nie istnieje!"
        }

    cursor.execute("""
        UPDATE Machines
        SET Name = ?,
            Description = ?,
            Picture = ?
        WHERE Id = ?
    """, (
        data.get("Name", "hstm"),
        data.get("Description", "5axis"),
        data.get("Picture", "test"),
        machine_id
    ))

    db.commit()

    return {
        "status": "ok"
    }


# =====================================================
# DODAWANIE MASZYNY
# =====================================================
@router.post("/add")
def add_machine(
    data: dict = Body(...),
    db=Depends(get_db)
):
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO Machines (
            Name,
            Description,
            Picture
        )
        VALUES (?, ?, ?)
    """, (
        data.get("Name", "hstm"),
        data.get("Description", "5axis"),
        data.get("Picture", "test")
    ))

    db.commit()

    return {
        "status": "ok",
        "id": cursor.lastrowid
    }


# =====================================================
# USUWANIE MASZYNY
# =====================================================
@router.post("/delete/{machine_id}")
def delete_machine(
    machine_id: int,
    db=Depends(get_db)
):
    cursor = db.cursor()

    existing = cursor.execute("""
        SELECT 1
        FROM Machines
        WHERE Id = ?
    """, (machine_id,)).fetchone()

    if not existing:
        return {
            "status": "error",
            "message": "Maszyna nie istnieje!"
        }

    cursor.execute("""
        DELETE FROM Machines
        WHERE Id = ?
    """, (machine_id,))

    db.commit()

    return {
        "status": "ok"
    }