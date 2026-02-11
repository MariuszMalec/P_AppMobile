from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from templates import templates
from db import get_db
from collections import defaultdict
from datetime import datetime, timedelta
import calendar
from fastapi import Form
from fastapi.responses import RedirectResponse


router = APIRouter(
    prefix="/harmonogram",
    tags=["harmonogram"]
)

@router.get("", response_class=HTMLResponse)
def harmonogram_page(request: Request, db=Depends(get_db)):
    cursor = db.cursor()

    # Pobierz maszyny
    machines = cursor.execute("SELECT * FROM Machines").fetchall()

    # Pobierz zamówienia i przypisz je do maszyn (zakładamy, że Orders już mają maszynę w ProjectName)
    orders = cursor.execute("""
        SELECT 
            Id, Name, Zlecenie, Haslo, ProjectName, TypeOfBlade,
            StartDate, Exw, Hours,
            ExistNC, ExistCMM, ExistMaterial,
            Id as MachineId
        FROM Orders
    """).fetchall()

    # Harmonogram dla każdej maszyny
    schedule = defaultdict(lambda: defaultdict(list))
    for o in orders:
        remaining_hours = o["Hours"]
        start_date = datetime.strptime(o["Exw"][:10], "%Y-%m-%d")
        machine_id = o["MachineId"]  # każda maszyna dostaje projekt
        while remaining_hours > 0:
            hours_for_day = min(24, remaining_hours)
            day_key = start_date.strftime("%Y-%m-%d")
            # Jeden projekt na maszynę na dzień
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
                "ExistMaterial": o["ExistMaterial"]
            })
            remaining_hours -= hours_for_day
            start_date += timedelta(days=1)

    # Bieżący miesiąc
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    num_days = calendar.monthrange(current_year, current_month)[1]

    # Tworzymy listę dni
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


@router.get("/edit/{order_id}", response_class=HTMLResponse)
def edit_order_page(order_id: int, request: Request, db=Depends(get_db)):
    cursor = db.cursor()

    order = cursor.execute(
        "SELECT * FROM Orders WHERE Id = ?",
        (order_id,)
    ).fetchone()

    return templates.TemplateResponse(
        "edit_order.html",
        {
            "request": request,
            "order": order
        }
    )


@router.post("/edit/{order_id}")
def update_order(
    order_id: int,
    StartDate: str = Form(...),
    Exw: str = Form(...),
    Hours: int = Form(...),
    ExistNC: int = Form(0),
    ExistCMM: int = Form(0),
    ExistMaterial: int = Form(0),
    db=Depends(get_db)
):
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
        StartDate,
        Exw,
        Hours,
        ExistNC,
        ExistCMM,
        ExistMaterial,
        order_id
    ))

    db.commit()

    return RedirectResponse(url="/harmonogram", status_code=303)

