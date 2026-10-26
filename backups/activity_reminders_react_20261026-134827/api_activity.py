from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db import get_db
from enums import DAY_NAMES
from validators import validate_activity_form, validate_activity_edit_form

router = APIRouter(prefix="/api/activities", tags=["api-activities"])

ALLOWED_REMINDER_MINUTES = {5, 10, 15, 30, 60}


class ActivityIn(BaseModel):
    day_of_week: int
    start: str
    end: str
    description: str = ""
    person_id: int
    picture_id: int
    reminder_enabled: bool = False
    reminder_minutes: int = 15


class ReminderSettingsIn(BaseModel):
    enabled: bool


def _validate_reminder(minutes: int):
    if minutes not in ALLOWED_REMINDER_MINUTES:
        raise HTTPException(
            status_code=400,
            detail={"errors": ["Wybierz przypomnienie: 5, 10, 15, 30 lub 60 minut."]},
        )


def _row_to_dict(r):
    return {
        "id": r["Id"],
        "dayOfWeek": r["DayOfWeek"],
        "dayName": DAY_NAMES.get(r["DayOfWeek"], "Nieznany"),
        "start": r["StartTime"],
        "end": r["EndTime"],
        "description": r["Description"],
        "personId": r["PersonId"],
        "personName": r["PersonName"],
        "pictureId": r["PictureId"],
        "pictureName": r["PictureName"],
        "picture": r["Picture"],
        "reminderEnabled": bool(r["ReminderEnabled"]),
        "reminderMinutes": r["ReminderMinutes"],
    }


BASE_QUERY = """
    SELECT
        ad.Id, ad.DayOfWeek, ad.StartTime, ad.EndTime, ad.Description,
        ad.ReminderEnabled, ad.ReminderMinutes,
        pf.Id AS PersonId, pf.PersonName,
        pa.Id AS PictureId, pa.Name AS PictureName, pa.Picture
    FROM ActiviesDays ad
    LEFT JOIN PersonFamilies pf ON ad.ModelPersonFamilyId = pf.Id
    LEFT JOIN PictureActivities pa ON ad.ModelPictureActivityId = pa.Id
"""


@router.get("")
def list_activities(db=Depends(get_db)):
    rows = db.execute(
        BASE_QUERY + " ORDER BY ad.DayOfWeek, ad.StartTime"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/meta")
def meta(db=Depends(get_db)):
    persons = [{"id": 0, "name": "RODZINA"}]
    for p in db.execute(
        "SELECT Id, PersonName FROM PersonFamilies ORDER BY Id"
    ):
        if p["Id"] != 5:
            persons.append({"id": p["Id"], "name": p["PersonName"]})

    pictures = [
        {"id": p["Id"], "name": p["Name"], "picture": p["Picture"]}
        for p in db.execute(
            "SELECT Id, Name, Picture FROM PictureActivities ORDER BY Name"
        )
    ]
    days = [{"id": k, "name": v} for k, v in DAY_NAMES.items() if k != 0]
    return {"persons": persons, "pictures": pictures, "days": days}


@router.get("/settings/reminders")
def get_reminder_settings(db=Depends(get_db)):
    row = db.execute(
        "SELECT Value FROM AppSettings WHERE Key = ?",
        ("global_notifications_enabled",),
    ).fetchone()
    return {"enabled": bool(int(row["Value"])) if row else True}


@router.put("/settings/reminders")
def update_reminder_settings(
    body: ReminderSettingsIn, db=Depends(get_db)
):
    db.execute(
        """INSERT INTO AppSettings (Key, Value) VALUES (?, ?)
           ON CONFLICT(Key) DO UPDATE SET Value = excluded.Value""",
        ("global_notifications_enabled", "1" if body.enabled else "0"),
    )
    db.commit()
    return {"enabled": body.enabled}


@router.get("/{activity_id}")
def get_activity(activity_id: int, db=Depends(get_db)):
    r = db.execute(
        BASE_QUERY + " WHERE ad.Id = ?", (activity_id,)
    ).fetchone()
    if not r:
        raise HTTPException(404, "Nie znaleziono aktywności")
    return _row_to_dict(r)


@router.post("", status_code=201)
def create_activity(body: ActivityIn, db=Depends(get_db)):
    _validate_reminder(body.reminder_minutes)

    pic = db.execute(
        "SELECT Name FROM PictureActivities WHERE Id = ?",
        (body.picture_id,),
    ).fetchone()
    if not pic:
        raise HTTPException(400, detail={"errors": ["Nieznana aktywność"]})

    errors, picture_id = validate_activity_form(
        body.start, body.end, body.day_of_week,
        body.person_id, pic["Name"], db
    )
    if errors:
        raise HTTPException(400, detail={"errors": errors})

    cur = db.execute(
        """INSERT INTO ActiviesDays
           (DayOfWeek, StartTime, EndTime, Description,
            ModelPersonFamilyId, ModelPictureActivityId,
            ReminderEnabled, ReminderMinutes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            body.day_of_week, body.start, body.end,
            body.description.strip() or None,
            5 if body.person_id == 0 else body.person_id,
            picture_id,
            int(body.reminder_enabled),
            body.reminder_minutes,
        ),
    )
    db.commit()
    return {"id": cur.lastrowid}


@router.put("/{activity_id}")
def update_activity(
    activity_id: int, body: ActivityIn, db=Depends(get_db)
):
    _validate_reminder(body.reminder_minutes)

    if not db.execute(
        "SELECT 1 FROM ActiviesDays WHERE Id = ?", (activity_id,)
    ).fetchone():
        raise HTTPException(404, "Nie znaleziono aktywności")

    person_id = 5 if body.person_id == 0 else body.person_id
    errors = validate_activity_edit_form(
        body.start, body.end, body.day_of_week, person_id, activity_id, db
    )
    if errors:
        raise HTTPException(400, detail={"errors": errors})

    pic = db.execute(
        "SELECT 1 FROM PictureActivities WHERE Id = ?", (body.picture_id,)
    ).fetchone()
    if not pic:
        raise HTTPException(400, detail={"errors": ["Nieznana aktywność"]})

    db.execute(
        """UPDATE ActiviesDays
           SET DayOfWeek=?, StartTime=?, EndTime=?, Description=?,
               ModelPersonFamilyId=?, ModelPictureActivityId=?,
               ReminderEnabled=?, ReminderMinutes=?
           WHERE Id=?""",
        (
            body.day_of_week, body.start, body.end,
            body.description.strip() or None, person_id, body.picture_id,
            int(body.reminder_enabled), body.reminder_minutes, activity_id,
        ),
    )
    db.commit()
    return {"status": "ok"}


@router.delete("/{activity_id}", status_code=204)
def delete_activity(activity_id: int, db=Depends(get_db)):
    db.execute("DELETE FROM ActiviesDays WHERE Id = ?", (activity_id,))
    db.commit()
