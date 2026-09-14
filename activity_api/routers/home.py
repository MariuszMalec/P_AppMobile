import traceback
from fastapi import APIRouter, Request, Form, Query, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.status import HTTP_303_SEE_OTHER
import sqlite3
from templates import templates
from enums import PERSON_ENUM_MAP
from validators import (    
    system_day_to_db_day,
)
from db import get_db
from datetime import datetime


router = APIRouter(
    prefix="/home",
    tags=["home"]
)


# ==============================
# HOME
# ==============================
@router.get("", response_class=HTMLResponse)
def home_page(
    request: Request,
    db=Depends(get_db)
):
    cursor = db.cursor()

    try:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        iso_day = now.isoweekday()
        current_day = system_day_to_db_day(iso_day)

        previous_iso_day = 7 if iso_day == 1 else iso_day - 1
        previous_day = system_day_to_db_day(previous_iso_day)

        current_day_name = now.strftime("%A")

        # DZISIAJ
        rows_today = cursor.execute("""
            SELECT
                ad.StartTime,
                ad.EndTime,
                ad.Description,
                pf.PersonName,
                pf.PersonPicture,
                pa.Picture
            FROM ActiviesDays ad
            LEFT JOIN PersonFamilies pf
                ON ad.ModelPersonFamilyId = pf.Id
            LEFT JOIN PictureActivities pa
                ON ad.ModelPictureActivityId = pa.Id
            WHERE ad.DayOfWeek = ?
            ORDER BY ad.StartTime
        """, (current_day,)).fetchall()

        # POPRZEDNI DZIEŃ - AKTYWNOŚCI PRZECHODZĄCE PRZEZ PÓŁNOC
        rows_previous = cursor.execute("""
            SELECT
                ad.StartTime,
                ad.EndTime,
                ad.Description,
                pf.PersonName,
                pf.PersonPicture,
                pa.Picture
            FROM ActiviesDays ad
            LEFT JOIN PersonFamilies pf
                ON ad.ModelPersonFamilyId = pf.Id
            LEFT JOIN PictureActivities pa
                ON ad.ModelPictureActivityId = pa.Id
            WHERE ad.DayOfWeek = ?
              AND time(ad.StartTime) > time(ad.EndTime)
              AND time(ad.EndTime) >= time(?)
            ORDER BY ad.StartTime
        """, (
            previous_day,
            current_time,
        )).fetchall()

        current_items = []
        next_items = []

        # AKTYWNE Z POPRZEDNIEGO DNIA
        for r in rows_previous:
            current_items.append({
                "start": r["StartTime"],
                "end": r["EndTime"],
                "description": r["Description"],
                "person": r["PersonName"],
                "personPicture": r["PersonPicture"],
                "picture": r["Picture"],
            })

        # DZISIAJ
        for r in rows_today:
            item = {
                "start": r["StartTime"],
                "end": r["EndTime"],
                "description": r["Description"],
                "person": r["PersonName"],
                "personPicture": r["PersonPicture"],
                "picture": r["Picture"],
            }

            if r["StartTime"] <= current_time <= r["EndTime"]:
                current_items.append(item)

            elif r["StartTime"] > current_time:
                next_items.append(item)

        current_items.sort(key=lambda x: x["start"])
        next_items.sort(key=lambda x: x["start"])

        print(
            f"HOME: time={current_time}, "
            f"current_day={current_day}, "
            f"previous_day={previous_day}, "
            f"CURRENT={len(current_items)}, "
            f"NEXT={len(next_items)}"
        )

        for item in current_items:
            print(
                "  CURRENT:",
                item["start"],
                item["end"],
                item["person"],
                item["description"]
            )

        return templates.TemplateResponse(
            request,
            "home.html",
            {
                "now": current_time,
                "current": current_items,
                "next": next_items,
                "current_day_name": current_day_name,
                "no_data": False,
            },
            status_code=200
        )

    except Exception as e:
        print("!!! HOME ERROR !!!")
        print(repr(e))

        return templates.TemplateResponse(
            request,
            "home.html",
            {
                "now": "",
                "current": [],
                "next": [],
                "current_day_name": "",
                "no_data": True,
            },
            status_code=400
        )

    finally:
        db.close()


@router.get("/homebyperson", response_class=HTMLResponse)
def home_page_by_person(
        request: Request,
        person: str = Query(default="MAMA"),
        db=Depends(get_db)
    ):

    cursor = db.cursor()

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    iso_day = now.isoweekday()
    current_day = system_day_to_db_day(iso_day)

    previous_iso_day = 7 if iso_day == 1 else iso_day - 1
    previous_day = system_day_to_db_day(previous_iso_day)

    current_day_name = now.strftime("%A")

    # ==============================
    # OSOBY Z BAZY
    # ==============================
    person_rows = cursor.execute("""
        SELECT Id, PersonName
        FROM PersonFamilies
        ORDER BY Id
    """).fetchall()

    persons = [
        r["PersonName"]
        for r in person_rows
    ]

    # ==============================
    # MAPA NAZWA -> ID
    # ==============================
    PERSON_STRING_TO_ID = {
        r["PersonName"]: r["Id"]
        for r in person_rows
    }

    # ==============================
    # WYBRANA OSOBA
    # ==============================
    if person in PERSON_STRING_TO_ID:
        selected_person = person
    elif "MAMA" in PERSON_STRING_TO_ID:
        selected_person = "MAMA"
    elif persons:
        selected_person = persons[0]
    else:
        selected_person = ""

    person_id = PERSON_STRING_TO_ID.get(selected_person)

    # ==============================
    # SQL - DZISIAJ
    # ==============================
    sql_today = """
        SELECT
            ad.StartTime,
            ad.EndTime,
            ad.Description,
            pf.PersonName,
            pf.PersonPicture,
            pa.Picture
        FROM ActiviesDays ad
        LEFT JOIN PersonFamilies pf
            ON ad.ModelPersonFamilyId = pf.Id
        LEFT JOIN PictureActivities pa
            ON ad.ModelPictureActivityId = pa.Id
        WHERE ad.DayOfWeek = ?
    """

    params_today = [current_day]

    # RODZINA = WSZYSTKIE OSOBY
    if selected_person != "RODZINA" and person_id is not None:
        sql_today += " AND ad.ModelPersonFamilyId = ?"
        params_today.append(person_id)

    sql_today += " ORDER BY ad.StartTime"

    rows_today = cursor.execute(
        sql_today,
        params_today
    ).fetchall()

    # ==============================
    # SQL - POPRZEDNI DZIEŃ
    # TYLKO PRZEJŚCIE PRZEZ PÓŁNOC
    # ==============================
    sql_previous = """
        SELECT
            ad.StartTime,
            ad.EndTime,
            ad.Description,
            pf.PersonName,
            pf.PersonPicture,
            pa.Picture
        FROM ActiviesDays ad
        LEFT JOIN PersonFamilies pf
            ON ad.ModelPersonFamilyId = pf.Id
        LEFT JOIN PictureActivities pa
            ON ad.ModelPictureActivityId = pa.Id
        WHERE ad.DayOfWeek = ?
          AND time(ad.StartTime) > time(ad.EndTime)
          AND time(ad.EndTime) >= time(?)
    """

    params_previous = [
        previous_day,
        current_time,
    ]

    if selected_person != "RODZINA" and person_id is not None:
        sql_previous += " AND ad.ModelPersonFamilyId = ?"
        params_previous.append(person_id)

    sql_previous += " ORDER BY ad.StartTime"

    rows_previous = cursor.execute(
        sql_previous,
        params_previous
    ).fetchall()

    db.close()

    current_items = []
    next_items = []

    # ==============================
    # TERAZ - POPRZEDNI DZIEŃ
    # PRZECHODZI PRZEZ PÓŁNOC
    # ==============================
    for r in rows_previous:
        current_items.append({
            "start": r["StartTime"],
            "end": r["EndTime"],
            "description": r["Description"],
            "person": r["PersonName"],
            "personPicture": r["PersonPicture"],
            "picture": r["Picture"],
        })

    # ==============================
    # DZISIAJ
    # ==============================
    for r in rows_today:

        item = {
            "start": r["StartTime"],
            "end": r["EndTime"],
            "description": r["Description"],
            "person": r["PersonName"],
            "personPicture": r["PersonPicture"],
            "picture": r["Picture"],
        }

        # TERAZ
        if r["StartTime"] <= current_time <= r["EndTime"]:
            current_items.append(item)

        # NASTĘPNIE
        elif r["StartTime"] > current_time:
            next_items.append(item)

    current_items.sort(key=lambda x: x["start"])
    next_items.sort(key=lambda x: x["start"])

    print(
        f"HOMEBYPERSON: person={selected_person}, "
        f"time={current_time}, "
        f"current_day={current_day}, "
        f"previous_day={previous_day}, "
        f"CURRENT={len(current_items)}, "
        f"NEXT={len(next_items)}"
    )

    for item in current_items:
        print(
            "  CURRENT:",
            item["start"],
            item["end"],
            item["person"],
            item["description"]
        )

    return templates.TemplateResponse(
        request,
        "statusbyperson.html",
        {
            "now": current_time,
            "current": current_items,
            "next": next_items,
            "current_day_name": current_day_name,
            "persons": persons,
            "selected_person": selected_person,
        }
    )

