from fastapi import APIRouter, Request, Depends
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

@router.get("", response_class=HTMLResponse)
def harmonogram_page(request: Request, db=Depends(get_db)):
    cursor = db.cursor()

    # Pobieramy zamówienia
    orders = cursor.execute("""
        SELECT
            Id,
            Name,
            Zlecenie,
            Haslo,
            ProjectName,
            TypeOfBlade,
            Exw,
            Hours,
            ExistNC,
            ExistCMM,
            ExistMaterial
        FROM Orders
    """).fetchall()

    # Pobieramy maszyny
    machines = cursor.execute(
        "SELECT * FROM Machines"
    ).fetchall()

    # Tworzymy harmonogram dzienny
    schedule = defaultdict(list)
    for o in orders:
        remaining_hours = o["Hours"]
        start_date = datetime.strptime(o["Exw"][:10], "%Y-%m-%d")
        while remaining_hours > 0:
            hours_for_day = min(24, remaining_hours)
            day_key = start_date.strftime("%Y-%m-%d")

            schedule[day_key].append({
                "Id": o["Id"],
                "Name": o["Name"],
                "Zlecenie": o["Zlecenie"],
                "Haslo": o["Haslo"],
                "ProjectName": o["ProjectName"],
                "TypeOfBlade": o["TypeOfBlade"],
                "Hours": hours_for_day,
                "ExistNC": o["ExistNC"],
                "ExistCMM": o["ExistCMM"],
                "ExistMaterial": o["ExistMaterial"]
            })

            remaining_hours -= hours_for_day
            start_date += timedelta(days=1)

    # Bieżący miesiąc i rok
    current_month = datetime.now().month
    current_year = datetime.now().year
    num_days = calendar.monthrange(current_year, current_month)[1]  # liczba dni w miesiącu

    days = []
    for day in range(1, num_days + 1):
        date_obj = datetime(current_year, current_month, day)
        date_str = date_obj.strftime("%Y-%m-%d")
        day_orders = schedule.get(date_str, [])
        total_hours = sum(o["Hours"] for o in day_orders)

        days.append({
            "number": day,
            "orders": day_orders,
            "total_hours": total_hours,
            "overload": total_hours > 24,
            "weekday": date_obj.weekday()  # 0=Pon, 6=Nd
        })

    return templates.TemplateResponse(
        "harmonogram.html",
        {
            "request": request,
            "days": days,
            "machines": machines
        }
    )
