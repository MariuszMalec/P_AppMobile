from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import HTMLResponse
from templates import templates
from db import get_db
from collections import defaultdict
from datetime import datetime, timedelta
import calendar
import hashlib

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
            StartDate, Exw, Hours, MachineId,
            ExistNC, ExistCMM, ExistMaterial,
            Color
        FROM Orders
    """).fetchall()

    schedule = defaultdict(lambda: defaultdict(list))

    def get_color(order_id):
        # Generujemy kolor na podstawie ID (jeśli brak koloru w bazie)
        h = hashlib.md5(str(order_id).encode()).hexdigest()
        return f"#{h[:6]}"

    for o in orders:
        remaining_hours = o["Hours"]
        start_date = datetime.strptime(o["StartDate"][:10], "%Y-%m-%d")
        machine_id = o["MachineId"]
        color = o["Color"] or get_color(o["Id"])

        while remaining_hours > 0:
            day_key = start_date.strftime("%Y-%m-%d")

            already_scheduled = sum(item["Hours"] for item in schedule[machine_id].get(day_key, []))
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
                    "Hours": hours_for_day,
                    "ExistNC": o["ExistNC"],
                    "ExistCMM": o["ExistCMM"],
                    "ExistMaterial": o["ExistMaterial"],
                    "StartDate": o["StartDate"],
                    "Exw": o["Exw"],
                    "MachineId": o["MachineId"],
                    "Color": color
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
        {"request": request, "machines": machines, "days": days, "schedule": schedule}
    )


# =====================================================
# DODAWANIE ORDERA
# =====================================================
@router.post("/add")
def add_order(data: dict = Body(...), db=Depends(get_db)):
    cursor = db.cursor()

    color = data.get("Color") or "#f4f4f4"

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
# EDYCJA ORDERA Z KONTROLĄ KONFLIKTÓW GODZINOWYCH
# =====================================================
@router.post("/edit/{order_id}")
def edit_order(order_id: int, data: dict = Body(...), db=Depends(get_db)):
    cursor = db.cursor()

    # Parsowanie daty startu
    new_start = datetime.fromisoformat(data["StartDate"])
    new_hours = int(data.get("Hours", 8))
    new_machine = data["MachineId"]

    # Pobierz wszystkie ordery w tej maszynie oprócz edytowanego
    other_orders = cursor.execute("""
        SELECT Id, StartDate, Hours FROM Orders
        WHERE MachineId = ? AND Id != ?
    """, (new_machine, order_id)).fetchall()

    # Sprawdzenie konfliktu godzinowego
    for o in other_orders:
        existing_start = datetime.fromisoformat(o["StartDate"])
        existing_end = existing_start + timedelta(hours=o["Hours"])
        new_end = new_start + timedelta(hours=new_hours)

        if (new_start < existing_end) and (new_end > existing_start):
            return {"status": "error", "message": f"Konflikt z orderem ID {o['Id']}!"}

    # Pobierz kolor z payload lub ustaw domyślny
    color = data.get("Color") or "#f4f4f4"

    # Aktualizacja ordera z zapisem wszystkich pól
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
        data["StartDate"],          # pełny datetime
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
