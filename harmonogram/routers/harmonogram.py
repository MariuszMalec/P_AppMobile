from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from templates import templates
from db import get_db
from collections import defaultdict
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/harmonogram",
    tags=["harmonogram"]
)

@router.get("", response_class=HTMLResponse)
def harmonogram_page(request: Request, db=Depends(get_db)):
    cursor = db.cursor()
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
    db.close()

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

    # Tworzymy listę dni miesiąca (1–31) z harmonogramem
    current_month = datetime.now().month
    current_year = datetime.now().year
    days = []
    for day in range(1, 32):
        date_str = f"{current_year}-{current_month:02d}-{day:02d}"
        day_orders = schedule.get(date_str, [])
        total_hours = sum(o["Hours"] for o in day_orders)
        days.append({
            "number": day,
            "orders": day_orders,
            "total_hours": total_hours,
            "overload": total_hours > 24
        })

    return templates.TemplateResponse(
        "harmonogram.html",
        {
            "request": request,
            "days": days
        }
    )
