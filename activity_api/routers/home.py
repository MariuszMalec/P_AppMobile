from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import HTMLResponse
from templates import templates
from validators import system_day_to_db_day
from db import get_db
from datetime import datetime


router = APIRouter(
    prefix="/home",
    tags=["home"]
)


def make_item(r):
    return {
        "start": r["StartTime"],
        "end": r["EndTime"],
        "description": r["Description"],
        "person": r["PersonName"],
        "personPicture": r["PersonPicture"],
        "picture": r["Picture"],
    }


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

        # ==============================
        # DZISIAJ
        # ==============================
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

        # ==============================
        # POPRZEDNI DZIEŃ
        # TYLKO AKTYWNOŚCI PRZECHODZĄCE
        # PRZEZ PÓŁNOC I NADAL TRWAJĄCE
        # ==============================
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

        # ==============================
        # TERAZ - POPRZEDNI DZIEŃ
        # ==============================
        for r in rows_previous:
            current_items.append(make_item(r))

        # ==============================
        # DZISIAJ
        # ==============================
        for r in rows_today:
            item = make_item(r)

            start = r["StartTime"]
            end = r["EndTime"]

            # ==============================
            # ZWYKŁA AKTYWNOŚĆ
            # np. 08:00 -> 10:00
            # ==============================
            if start <= end:

                if start <= current_time <= end:
                    current_items.append(item)

                elif start > current_time:
                    next_items.append(item)

                continue

            # ==============================
            # AKTYWNOŚĆ PRZECHODZĄCA PRZEZ PÓŁNOC
            # np. 23:00 -> 06:45
            #
            # Jeżeli jest zapisana na DZISIAJ:
            #
            # 05:55 -> jeszcze się nie rozpoczęła
            #          => NASTĘPNIE
            #
            # 23:30 -> już trwa
            #          => TERAZ
            # ==============================
            if start > end:

                if current_time >= start:
                    current_items.append(item)

                elif current_time < start:
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


# ==============================
# HOME BY PERSON
# ==============================
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

    person_string_to_id = {
        r["PersonName"]: r["Id"]
        for r in person_rows
    }

    # ==============================
    # WYBRANA OSOBA
    # ==============================
    if person in person_string_to_id:
        selected_person = person
    elif "MAMA" in person_string_to_id:
        selected_person = "MAMA"
    elif persons:
        selected_person = persons[0]
    else:
        selected_person = ""

    person_id = person_string_to_id.get(selected_person)

    # ==============================
    # DZISIAJ
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

    if selected_person != "RODZINA" and person_id is not None:
        sql_today += " AND ad.ModelPersonFamilyId = ?"
        params_today.append(person_id)

    sql_today += " ORDER BY ad.StartTime"

    rows_today = cursor.execute(
        sql_today,
        params_today
    ).fetchall()

    # ==============================
    # POPRZEDNI DZIEŃ
    # TYLKO PRZEJŚCIE PRZEZ PÓŁNOC
    # I TYLKO AKTYWNOŚCI NADAL TRWAJĄCE
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
    # ==============================
    for r in rows_previous:
        current_items.append(make_item(r))

    # ==============================
    # DZISIAJ
    # ==============================
    for r in rows_today:
        item = make_item(r)

        start = r["StartTime"]
        end = r["EndTime"]

        # ==============================
        # ZWYKŁA AKTYWNOŚĆ
        # ==============================
        if start <= end:

            if start <= current_time <= end:
                current_items.append(item)

            elif start > current_time:
                next_items.append(item)

            continue

        # ==============================
        # AKTYWNOŚĆ PRZECHODZĄCA PRZEZ PÓŁNOC
        #
        # Dzisiejsza:
        # 23:00 -> 06:45
        #
        # 05:55 = NASTĘPNIE
        # 23:30 = TERAZ
        # ==============================
        if start > end:

            if current_time >= start:
                current_items.append(item)

            elif current_time < start:
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
