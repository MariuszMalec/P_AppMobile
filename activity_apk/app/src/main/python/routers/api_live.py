from typing import Optional

from fastapi import APIRouter, Depends, Query

from db import get_db
from validators import hhmm
from routers.livenow import is_time_in_range, get_current_day_info

router = APIRouter(prefix="/api/live", tags=["api-live"])

DAY_NAMES = {
    1: "Niedziela", 2: "Poniedzialek", 3: "Wtorek", 4: "Sroda",
    5: "Czwartek", 6: "Piatek", 7: "Sobota",
}

SELECT = """
    SELECT
        ad.Id, ad.DayOfWeek, ad.StartTime, ad.EndTime, ad.Description,
        pf.Id AS PersonId,
        pa.Id AS PictureId, pa.Name AS PictureName, pa.Picture
    FROM ActiviesDays ad
    LEFT JOIN PersonFamilies pf ON ad.ModelPersonFamilyId = pf.Id
    LEFT JOIN PictureActivities pa ON ad.ModelPictureActivityId = pa.Id
"""


def _cell(r, is_live):
    return {
        "id": r["Id"],
        "dayOfWeek": r["DayOfWeek"],
        "start": r["StartTime"],
        "end": r["EndTime"],
        "description": r["Description"],
        "personId": r["PersonId"],
        "pictureId": r["PictureId"],
        "pictureName": r["PictureName"],
        "picture": r["Picture"],
        "isLive": is_live,
    }


@router.get("/status")
def live_status(day: Optional[int] = Query(None), db=Depends(get_db)):
    now, iso_day, today, previous_day, current_time = get_current_day_info()

    if day is None or day < 1 or day > 7:
        day = today
    is_today = day == today

    persons = [
        {"id": p["Id"], "name": p["PersonName"]}
        for p in db.execute("SELECT Id, PersonName FROM PersonFamilies ORDER BY Id")
    ]
    person_ids = [p["id"] for p in persons]

    rows_day = db.execute(
        SELECT + " WHERE ad.DayOfWeek = ? ORDER BY ad.StartTime", (day,)
    ).fetchall()

    # wpisy z poprzedniego dnia, które trwają przez północ (tylko dla "dzisiaj")
    rows_prev = []
    if is_today:
        rows_prev = db.execute(
            SELECT + """ WHERE ad.DayOfWeek = ?
                AND time(ad.StartTime) > time(ad.EndTime)
                AND time(ad.EndTime) >= time(?)
                ORDER BY ad.StartTime""",
            (previous_day, current_time),
        ).fetchall()

    table = {}

    def put(r, is_live):
        key = f'{hhmm(r["StartTime"])} – {hhmm(r["EndTime"])}'
        row = table.setdefault(
            key,
            {"time": key, "start": hhmm(r["StartTime"]), "cells": {pid: None for pid in person_ids}},
        )
        if r["PersonId"] in row["cells"]:
            row["cells"][r["PersonId"]] = _cell(r, is_live)

    for r in rows_prev:
        put(r, True)
    for r in rows_day:
        put(r, is_today and is_time_in_range(r["StartTime"], r["EndTime"], current_time))

    rows = [
        {"time": v["time"], "cells": [v["cells"][pid] for pid in person_ids]}
        for v in table.values()
    ]

    return {
        "day": day,
        "dayName": DAY_NAMES.get(day, ""),
        "today": today,
        "isToday": is_today,
        "now": current_time[:5],
        "persons": persons,
        "rows": rows,
    }


NOW_SELECT = """
    SELECT
        ad.Id, ad.StartTime, ad.EndTime, ad.Description,
        pf.PersonName, pf.PersonPicture,
        pa.Name AS PictureName, pa.Picture
    FROM ActiviesDays ad
    LEFT JOIN PersonFamilies pf ON ad.ModelPersonFamilyId = pf.Id
    LEFT JOIN PictureActivities pa ON ad.ModelPictureActivityId = pa.Id
"""


@router.get("/now")
def live_now(db=Depends(get_db)):
    now, iso_day, today, previous_day, current_time = get_current_day_info()

    rows_today = db.execute(
        NOW_SELECT + " WHERE ad.DayOfWeek = ? ORDER BY ad.StartTime", (today,)
    ).fetchall()

    rows_prev = db.execute(
        NOW_SELECT + """ WHERE ad.DayOfWeek = ?
            AND time(ad.StartTime) > time(ad.EndTime)
            AND time(ad.EndTime) >= time(?)
            ORDER BY ad.StartTime""",
        (previous_day, current_time),
    ).fetchall()

    def item(r):
        return {
            "id": r["Id"],
            "person": r["PersonName"],
            "personPicture": r["PersonPicture"],
            "description": r["Description"],
            "pictureName": r["PictureName"],
            "picture": r["Picture"],
            "start": hhmm(r["StartTime"]),
            "end": hhmm(r["EndTime"]),
        }

    items = [item(r) for r in rows_prev]
    items += [
        item(r) for r in rows_today
        if is_time_in_range(r["StartTime"], r["EndTime"], current_time)
    ]
    items.sort(key=lambda x: x["start"])

    return {
        "dayName": DAY_NAMES.get(today, ""),
        "now": current_time[:5],
        "items": items,
    }
