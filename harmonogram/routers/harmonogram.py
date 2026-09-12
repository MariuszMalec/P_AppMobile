from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import HTMLResponse
from templates import templates
from db import get_db
from collections import defaultdict
from datetime import datetime, timedelta
import calendar
import hashlib
import random

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

    # Pobranie maszyn
    machines = cursor.execute("SELECT * FROM Machines").fetchall()

    # Pobranie zamówień
    orders = cursor.execute("""
        SELECT 
            Id, Name, Zlecenie, Haslo, ProjectName, TypeOfBlade,
            StartDate, Exw, Hours, MachineId,
            ExistNC, ExistCMM, ExistMaterial,
            Color
        FROM Orders
        ORDER BY StartDate, Id
    """).fetchall()

    schedule = defaultdict(lambda: defaultdict(list))

    def get_color(order_id):
        h = hashlib.md5(str(order_id).encode()).hexdigest()
        return f"#{h[:6]}"

    # Lista orderów do wstawienia (kolejka)
    pending_orders = orders.copy()

    # Wypełnianie harmonogramu
    while pending_orders:
        o = pending_orders.pop(0)
        remaining_hours = o["Hours"]
        start_date = datetime.strptime(o["StartDate"][:10], "%Y-%m-%d")
        machine_id = o["MachineId"]
        color = o["Color"] or get_color(o["Id"])

        current_date = start_date

        while remaining_hours > 0:
            day_key = current_date.strftime("%Y-%m-%d")
            already_scheduled = sum(item["DayHours"] for item in schedule[machine_id].get(day_key, []))
            available_hours = max(0, 24 - already_scheduled)

            if available_hours > 0:
                hours_for_day = min(available_hours, remaining_hours)
                schedule[machine_id][day_key].append({
                    "Id": o["Id"],
                    "Name": o["Name"],
                    "Zlecenie": o["Zlecenie"],
                    "Haslo": o["Haslo"],
                    "ProjectName": o["ProjectName"] or "",
                    "TypeOfBlade": o["TypeOfBlade"],

                    "Hours": o["Hours"],          # całkowity czas orderu
                    "DayHours": hours_for_day,    # przydzielone na ten dzień

                    "ExistNC": o["ExistNC"],
                    "ExistCMM": o["ExistCMM"],
                    "ExistMaterial": o["ExistMaterial"],
                    "StartDate": o["StartDate"],
                    "Exw": o["Exw"],
                    "MachineId": o["MachineId"],
                    "Color": color
                })
                remaining_hours -= hours_for_day

            current_date += timedelta(days=1)

    # Tworzenie listy dni bieżącego miesiąca
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
        request,
        "harmonogram.html",
        {
            "machines": machines,
            "days": days,
            "schedule": schedule,
        }
    )





# =====================================================
# DODAWANIE ORDERA
# =====================================================
@router.post("/add")
def add_order(data: dict = Body(...), db=Depends(get_db)):
    cursor = db.cursor()

    # Losowy kolor dla nowego ordera
    colors = [
        "#FFCCCC",
        "#CCFFCC",
        "#CCCCFF",
        "#FFFFCC",
        "#FFCCFF",
        "#CCFFFF",
        "#FFD9B3",
        "#D9B3FF",
        "#B3E6FF",
        "#E6FFB3",
    ]

    color = random.choice(colors)

    cursor.execute("""
        INSERT INTO Orders (
            MachineId,
            StartDate,
            ProjectName,
            Zlecenie,
            Hours,
            Exw,
            ExistNC,
            ExistCMM,
            ExistMaterial,
            Color
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["MachineId"],
        data["StartDate"],
        data.get("ProjectName", ""),
        data.get("Zlecenie", ""),
        data.get("Hours", 8),
        data.get("Exw"),
        data.get("ExistNC", 0),
        data.get("ExistCMM", 0),
        data.get("ExistMaterial", 0),
        color
    ))

    db.commit()
    return {"status": "ok"}



# =====================================================
# EDYCJA ORDERA
# =====================================================
@router.post("/edit/{order_id}")
def edit_order(order_id: int, data: dict = Body(...), db=Depends(get_db)):
    cursor = db.cursor()

    # -------------------------------------------------
    # Dane z formularza
    # -------------------------------------------------
    new_machine = int(data["MachineId"])
    new_start = data["StartDate"]
    new_hours = int(data.get("Hours", 8))

    if new_hours < 1:
        new_hours = 1

    color = data.get("Color") or "#f4f4f4"

    # -------------------------------------------------
    # EDYCJA
    #
    # UWAGA:
    # NIE sprawdzamy tutaj konfliktu godzinowego!
    #
    # Dokładnie tak samo działa Drag & Drop:
    # zapisujemy nową maszynę i datę,
    # a harmonogram_page() sam później
    # rozłoży ordery i przesunie pozostałe w prawo.
    # -------------------------------------------------
    cursor.execute("""
        UPDATE Orders
        SET MachineId = ?,
            StartDate = ?,
            Exw = ?,
            Hours = ?,
            ExistNC = ?,
            ExistCMM = ?,
            ExistMaterial = ?,
            Zlecenie = ?,
            ProjectName = ?,
            Color = ?
        WHERE Id = ?
    """, (
        new_machine,
        new_start,
        data.get("Exw", None),
        new_hours,
        data.get("ExistNC", 0),
        data.get("ExistCMM", 0),
        data.get("ExistMaterial", 0),
        data.get("Zlecenie", ""),
        data.get("ProjectName", ""),
        color,
        order_id
    ))

    db.commit()

    return {"status": "ok"}


# =====================================================
# PRZENOSZENIE ORDERA (DRAG & DROP)
# =====================================================
@router.post("/move/{order_id}")
def move_order(order_id: int, data: dict = Body(...), db=Depends(get_db)):
    cursor = db.cursor()

    # Sprawdzamy, ile godzin są już zaplanowane w danym dniu na tej maszynie
    existing_hours = cursor.execute("""
        SELECT SUM(Hours)
        FROM Orders
        WHERE MachineId = ? AND StartDate = ?
    """, (data["MachineId"], data["StartDate"])).fetchone()[0] or 0

    # Sprawdzamy, czy dostępne godziny w danym dniu pozwalają na przeniesienie orderu
    if existing_hours + data.get("Hours", 0) > 24:
        return {"status": "error", "message": "Nie ma wystarczającej liczby godzin w tym dniu!"}

    # Jeśli w dniu jest wystarczająco miejsca, to wykonujemy przeniesienie orderu
    cursor.execute("""
        UPDATE Orders
        SET MachineId = ?, StartDate = ?
        WHERE Id = ?
    """, (data["MachineId"], data["StartDate"], order_id))

    db.commit()

    return {"status": "ok"}



# =====================================================
# USUWANIE ORDERA
# =====================================================
@router.post("/delete/{order_id}")
def delete_order(order_id: int, db=Depends(get_db)):
    cursor = db.cursor()

    existing = cursor.execute("SELECT 1 FROM Orders WHERE Id = ?", (order_id,)).fetchone()
    if not existing:
        return {"status": "error", "message": "Order nie istnieje!"}

    cursor.execute("DELETE FROM Orders WHERE Id = ?", (order_id,))
    db.commit()
    return {"status": "ok"}
