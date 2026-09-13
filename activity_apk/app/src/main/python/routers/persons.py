from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from db import get_db
from templates import templates


router = APIRouter(
    prefix="/persons",
    tags=["persons"]
)


# ============================================================
# LISTA OSÓB
# ============================================================
@router.get("", response_class=HTMLResponse)
def persons_page(
    request: Request,
    db=Depends(get_db)
):
    cursor = db.cursor()

    persons = cursor.execute("""
        SELECT
            Id,
            PersonName,
            PersonPicture
        FROM PersonFamilies
        ORDER BY Id
    """).fetchall()

    return templates.TemplateResponse(
        request,
        "persons.html",
        {
            "persons": persons
        }
    )


# ============================================================
# DODAWANIE OSOBY
# ============================================================
@router.post("/add")
def add_person(
    person_name: str = Form(...),
    person_picture: str = Form(""),
    db=Depends(get_db)
):
    person_name = person_name.strip()
    person_picture = person_picture.strip()

    if not person_name:
        return RedirectResponse(
            "/persons",
            status_code=303
        )

    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO PersonFamilies (
                PersonName,
                PersonPicture
            )
            VALUES (?, ?)
        """, (
            person_name,
            person_picture or None
        ))

        db.commit()

    except Exception:
        db.rollback()

    return RedirectResponse(
        "/persons",
        status_code=303
    )


# ============================================================
# EDYCJA OSOBY
# ============================================================
@router.post("/edit/{person_id}")
def edit_person(
    person_id: int,
    person_name: str = Form(...),
    person_picture: str = Form(""),
    db=Depends(get_db)
):
    person_name = person_name.strip()
    person_picture = person_picture.strip()

    if not person_name:
        return RedirectResponse(
            "/persons",
            status_code=303
        )

    cursor = db.cursor()

    try:
        cursor.execute("""
            UPDATE PersonFamilies
            SET
                PersonName = ?,
                PersonPicture = ?
            WHERE Id = ?
        """, (
            person_name,
            person_picture or None,
            person_id
        ))

        db.commit()

    except Exception:
        db.rollback()

    return RedirectResponse(
        "/persons",
        status_code=303
    )


# ============================================================
# USUWANIE OSOBY
# ============================================================
@router.post("/delete/{person_id}")
def delete_person(
    person_id: int,
    db=Depends(get_db)
):
    cursor = db.cursor()

    try:
        cursor.execute("""
            DELETE FROM PersonFamilies
            WHERE Id = ?
        """, (person_id,))

        db.commit()

    except Exception:
        db.rollback()

    return RedirectResponse(
        "/persons",
        status_code=303
    )
