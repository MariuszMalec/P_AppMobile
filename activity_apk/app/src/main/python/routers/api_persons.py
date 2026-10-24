import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db import get_db

router = APIRouter(prefix="/api/persons", tags=["api-persons"])

FAMILY_ID = 5  # RODZINA - wpis specjalny


class PersonIn(BaseModel):
    name: str
    picture: str = ""


LIST_QUERY = """
    SELECT pf.Id, pf.PersonName, pf.PersonPicture,
           COUNT(ad.Id) AS ActivityCount
    FROM PersonFamilies pf
    LEFT JOIN ActiviesDays ad ON ad.ModelPersonFamilyId = pf.Id
"""


def _dict(r):
    return {
        "id": r["Id"],
        "name": r["PersonName"],
        "picture": r["PersonPicture"],
        "activityCount": r["ActivityCount"],
        "protected": r["Id"] == FAMILY_ID,
    }


@router.get("")
def list_persons(db=Depends(get_db)):
    rows = db.execute(LIST_QUERY + " GROUP BY pf.Id ORDER BY pf.Id").fetchall()
    return [_dict(r) for r in rows]


@router.post("", status_code=201)
def create_person(body: PersonIn, db=Depends(get_db)):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, detail={"errors": ["Podaj nazwę osoby"]})
    try:
        cur = db.execute(
            "INSERT INTO PersonFamilies (PersonName, PersonPicture) VALUES (?, ?)",
            (name, body.picture.strip() or None),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise HTTPException(400, detail={"errors": [f"Osoba „{name}” już istnieje"]})
    return {"id": cur.lastrowid}


@router.put("/{person_id}")
def update_person(person_id: int, body: PersonIn, db=Depends(get_db)):
    row = db.execute(
        "SELECT PersonName FROM PersonFamilies WHERE Id = ?", (person_id,)
    ).fetchone()
    if not row:
        raise HTTPException(404, "Nie znaleziono osoby")

    name = body.name.strip()
    if person_id == FAMILY_ID:
        name = row["PersonName"]  # nazwy RODZINA nie zmieniamy
    if not name:
        raise HTTPException(400, detail={"errors": ["Podaj nazwę osoby"]})

    try:
        db.execute(
            "UPDATE PersonFamilies SET PersonName = ?, PersonPicture = ? WHERE Id = ?",
            (name, body.picture.strip() or None, person_id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise HTTPException(400, detail={"errors": [f"Osoba „{name}” już istnieje"]})
    return {"status": "ok"}


@router.delete("/{person_id}", status_code=204)
def delete_person(person_id: int, db=Depends(get_db)):
    if person_id == FAMILY_ID:
        raise HTTPException(400, detail={"errors": ["Nie można usunąć wpisu RODZINA"]})
    db.execute("DELETE FROM PersonFamilies WHERE Id = ?", (person_id,))
    db.commit()

