from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import HTMLResponse
from templates import templates
from db import get_db
from collections import defaultdict
from datetime import datetime, timedelta
import calendar

router = APIRouter(
    prefix="/harmonogram",
    tags=["harmonogram"]
)

# =====================================================
# GŁÓWNA STRONA HARMONOGRAMU
# =====================================================

@router.get("", response_class=HTMLResponse)
def harmonogram_page(request: Request, db=Depends(get_db)):
    cursor = db.cursor()

    machines = cursor.execute("SELECT * FROM Machines").fetchall()

    orders = cursor.execute("""
        SELECT 
            Id, Name, Zlecenie, Haslo, ProjectName, TypeOfBlade,
            StartDate, Exw, Hours,
            ExistNC, ExistCMM, ExistMaterial,
            Id as MachineId
        FROM Orders
    """).fetchall()

    schedule = defaultdict(lambda: defaultdict(list))

    for o in orders:
        remaining_hours = o["Hours"]

        # 🔥 PLANUJEMY OD StartDate
        start_date = datetime.strptime(o["StartDate"][:10], "%Y-%m-%d")
        machine_id = o["MachineId"]

        while remaining_hours > 0:
            hours_for_day = min(24, remaining_hours)
            day_key = start_date.strftime("%Y-%m-%d")

            schedule[machine_id][day_key].append({
                "Id": o["Id"],
                "Name": o["Name"],
                "Zlecenie": o["Zlecenie"],
                "Haslo": o["Haslo"],
                "ProjectName": o["ProjectName"],
                "TypeOfBlade": o["TypeOfBlade"],
                "Hours": hours_for_day,
                "ExistNC": o["ExistNC"],
                "ExistCMM": o["ExistCMM"],
                "ExistMaterial": o["ExistMaterial"],
                "StartDate": o["StartDate"],
                "Exw": o["Exw"]
            })

            remaining_hours -= hours_for_day
            start_date += timedelta(days=1)

    now = datetime.now()
    current_year = now.year
    current_month = now.month
    num_days = calendar.monthrange(current_year, current_month)[1]

    days = []
    for day in range(1, num_days + 1):
        date_obj = datetime(current_year, current_month, day)
        date_str = date_obj.strftime("%Y-%m-%d")
        days.append({
            "number": day,
            "date": date_obj,
            "weekday": date_obj.weekday(),
            "is_today": date_obj.date() == now.date(),
            "date_str": date_str
        })

    return templates.TemplateResponse(
        "harmonogram.html",
        {
            "request": request,
            "machines": machines,
            "days": days,
            "schedule": schedule
        }
    )

# =====================================================
# EDYCJA (JSON - pod modal)
# =====================================================

@router.post("/edit/{order_id}")
def update_order(order_id: int, data: dict = Body(...), db=Depends(get_db)):
    cursor = db.cursor()

    cursor.execute("""
        UPDATE Orders
        SET StartDate = ?,
            Exw = ?,
            Hours = ?,
            ExistNC = ?,
            ExistCMM = ?,
            ExistMaterial = ?
        WHERE Id = ?
    """, (
        data["StartDate"],
        data["Exw"],
        int(data["Hours"]),
        int(data["ExistNC"]),
        int(data["ExistCMM"]),
        int(data["ExistMaterial"]),
        order_id
    ))

    db.commit()
    return {"status": "ok"}

# =====================================================
# DRAG & DROP - PRZENOSZENIE
# =====================================================

@router.post("/move/{order_id}")
def move_order(order_id: int, data: dict = Body(...), db=Depends(get_db)):
    cursor = db.cursor()

    cursor.execute("""
        UPDATE Orders
        SET StartDate = ?
        WHERE Id = ?
    """, (
        data["StartDate"],
        order_id
    ))

    db.commit()
    return {"status": "moved"}
