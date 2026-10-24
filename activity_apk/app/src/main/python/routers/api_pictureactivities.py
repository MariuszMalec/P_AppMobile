import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db import get_db
from enums import ACTIVITY_ENUM_MAP

router = APIRouter(prefix="/api/pictureactivities", tags=["api-pictureactivities"])

OTHER_ID = next(
    (k for k, v in ACTIVITY_ENUM_MAP.items() if str(v.value).strip().lower() == "inne"),
    None,
)


class PictureCreate(BaseModel):
    activity_type: int
    name: str
    picture: str = ""


class PictureUpdate(BaseModel):
    picture: str = ""


LIST_QUERY = """
    SELECT pa.Id, pa.ActivityName, pa.Name, pa.Picture,
           COUNT(ad.Id) AS UsageCount
    FROM PictureActivities pa
    LEFT JOIN ActiviesDays ad ON ad.ModelPictureActivityId = pa.Id
"""


def _dict(r):
    return {
        "id": r["Id"],
        "activityType": r["ActivityName"],
        "name": r["Name"],
        "picture": r["Picture"],
        "usageCount": r["UsageCount"],
    }


@router.get("")
def list_items(db=Depends(get_db)):
    rows = db.execute(LIST_QUERY + " GROUP BY pa.Id ORDER BY pa.Id").fetchall()
    return [_dict(r) for r in rows]


# /types musi byc przed /{item_id}
@router.get("/types")
def types(db=Depends(get_db)):
    used = {r["ActivityName"] for r in db.execute("SELECT ActivityName FROM PictureActivities")}
    return [
        {
            "id": k,
            "label": v.value,
            "used": k in used and k != OTHER_ID,
            "isOther": k == OTHER_ID,
        }
        for k, v in ACTIVITY_ENUM_MAP.items()
    ]


@router.post("", status_code=201)
def create_item(body: PictureCreate, db=Depends(get_db)):
    name = body.name.strip()
    errors = []
    if not name:
        errors.append("Nazwa jest wymagana")
    elif len(name) > 15:
        errors.append("Nazwa moze miec maksymalnie 15 znakow")
    if body.activity_type not in ACTIVITY_ENUM_MAP:
        errors.append("Nieznany typ aktywnosci")
    if errors:
        raise HTTPException(400, detail={"errors": errors})

    if db.execute("SELECT 1 FROM PictureActivities WHERE Name = ?", (name,)).fetchone():
        raise HTTPException(400, detail={"errors": ["Taka nazwa aktywnosci juz istnieje"]})

    activity_type = body.activity_type
    if activity_type == OTHER_ID:
        activity_type = db.execute(
            "SELECT COALESCE(MAX(ActivityName), 0) + 1 FROM PictureActivities"
        ).fetchone()[0]

    try:
        cur = db.execute(
            "INSERT INTO PictureActivities (ActivityName, Name, Picture) VALUES (?, ?, ?)",
            (activity_type, name, body.picture.strip() or None),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise HTTPException(400, detail={"errors": ["Ten typ aktywnosci ma juz przypisany obrazek"]})
    return {"id": cur.lastrowid}


@router.put("/{item_id}")
def update_item(item_id: int, body: PictureUpdate, db=Depends(get_db)):
    if not db.execute("SELECT 1 FROM PictureActivities WHERE Id = ?", (item_id,)).fetchone():
        raise HTTPException(404, "Nie znaleziono rekordu")
    db.execute(
        "UPDATE PictureActivities SET Picture = ? WHERE Id = ?",
        (body.picture.strip() or None, item_id),
    )
    db.commit()
    return {"status": "ok"}


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db=Depends(get_db)):
    db.execute("DELETE FROM PictureActivities WHERE Id = ?", (item_id,))
    db.commit()
