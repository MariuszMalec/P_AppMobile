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


def next_position(cursor):
    """Pozycja na końcu kolejki (order wchodzi ostatni w swoim dniu)."""
    return cursor.execute(
        "SELECT COALESCE(MAX(Position), 0) + 1 FROM Orders"
    ).fetchone()[0]


def first_position(cursor):
    """Pozycja przed wszystkimi innymi (order wchodzi pierwszy w swoim dniu)."""
    return cursor.execute(
        "SELECT COALESCE(MIN(Position), 0) - 1 FROM Orders"
    ).fetchone()[0]


def clean_blade(value):
    """TypeOfBlade z formularza: tekst bez spacji na brzegach."""
    return str(value or "").strip()


# =====================================================
# GŁÓWNA STRONA HARMONOGRAMU
# =====================================================
@router.get("", response_class=HTMLResponse)
def harmonogram_page(request: Request, db=Depends(get_db)):
    cursor = db.cursor()

    # Pobranie maszyn
    machines = cursor.execute("SELECT * FROM Machines").fetchall()

    # Kolejność: najpierw data startu, w obrębie tego samego dnia Position.
    # Order z niższą Position zajmuje godziny pierwszy, a pozostałe
    # (z tego dnia i późniejsze) przesuwają się w prawo.
    orders = cursor.execute("""
        SELECT 
            Id, Name, Zlecenie, Haslo, ProjectName, TypeOfBlade,
            StartDate, Exw, Hours, MachineId,
            ExistNC, ExistCMM, ExistMaterial,
            Color
        FROM Orders
        ORDER BY substr(StartDate, 1, 10), Position, Id
    """).fetchall()

    schedule = defaultdict(lambda: defaultdict(list))

    def get_color(order_id):
        h = hashlib.md5(str(order_id).encode()).hexdigest()
        return f"#{h[:6]}"

    # Lista orderów do wstawienia (kolejka)
    pending_orders = list(orders)

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
            already_scheduled = sum(
                item["DayHours"] for item in schedule[machine_id].get(day_key, [])
            )
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
            TypeOfBlade,
            Hours,
            Exw,
            ExistNC,
            ExistCMM,
            ExistMaterial,
            Color,
            Position
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["MachineId"],
        data["StartDate"],
        data.get("ProjectName", ""),
        data.get("Zlecenie", ""),
        clean_blade(data.get("TypeOfBlade")),
        data.get("Hours", 8),
        data.get("Exw") or "",
        data.get("ExistNC", 0),
        data.get("ExistCMM", 0),
        data.get("ExistMaterial", 0),
        color,
        next_position(cursor)
    ))

    db.commit()
    return {"status": "ok"}


# =====================================================
# EDYCJA ORDERA
# =====================================================
@router.post("/edit/{order_id}")
def edit_order(order_id: int, data: dict = Body(...), db=Depends(get_db)):
    cursor = db.cursor()

    new_machine = int(data["MachineId"])
    new_start = data["StartDate"]
    new_hours = int(data.get("Hours", 8))

    if new_hours < 1:
        new_hours = 1

    color = data.get("Color") or "#f4f4f4"

    old = cursor.execute(
        "SELECT MachineId, StartDate, Position FROM Orders WHERE Id = ?",
        (order_id,)
    ).fetchone()

    if not old:
        return {"status": "error", "message": "Order nie istnieje!"}

    # Jeśli zmieniono maszynę lub datę startu, order działa jak przy
    # drag & drop: wchodzi pierwszy w nowym dniu i przesuwa pozostałe
    # w prawo. W przeciwnym razie (np. zmiana koloru, godzin)
    # zostaje na swojej pozycji.
    moved = (
        old["MachineId"] != new_machine
        or (old["StartDate"] or "")[:10] != new_start[:10]
    )
    position = first_position(cursor) if moved else old["Position"]

    # Bez sprawdzania konfliktu godzinowego - harmonogram_page()
    # sam rozłoży ordery i przesunie pozostałe w prawo.
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
            TypeOfBlade = ?,
            Color = ?,
            Position = ?
        WHERE Id = ?
    """, (
        new_machine,
        new_start,
        data.get("Exw") or "",
        new_hours,
        data.get("ExistNC", 0),
        data.get("ExistCMM", 0),
        data.get("ExistMaterial", 0),
        data.get("Zlecenie", ""),
        data.get("ProjectName", ""),
        clean_blade(data.get("TypeOfBlade")),
        color,
        position,
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

    order = cursor.execute(
        "SELECT 1 FROM Orders WHERE Id = ?", (order_id,)
    ).fetchone()

    if not order:
        return {"status": "error", "message": "Order nie istnieje!"}

    # Przeniesiony order wchodzi PIERWSZY w dniu docelowym (najniższa
    # Position). Ordery, które tam były, i wszystkie następne przesuwają
    # się w prawo, bo harmonogram liczy kolejkę wg (data, Position).
    # Brak limitu 24h: harmonogram sam rozkłada godziny (max 24h/dzień).
    cursor.execute("""
        UPDATE Orders
        SET MachineId = ?, StartDate = ?, Position = ?
        WHERE Id = ?
    """, (data["MachineId"], data["StartDate"], first_position(cursor), order_id))

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


# =====================================================
# ODCZYT HARMONOGRAMU DLA REACT
# =====================================================
@router.get("/api")
def harmonogram_api(db=Depends(get_db)):
    cursor = db.cursor()

    machines = cursor.execute("""
        SELECT Id, Name, Description, Picture
        FROM Machines
        ORDER BY Id
    """).fetchall()

    orders = cursor.execute("""
        SELECT
            Id, Name, Zlecenie, Haslo, ProjectName, TypeOfBlade,
            StartDate, Exw, Hours, MachineId,
            ExistNC, ExistCMM, ExistMaterial, Color, Position
        FROM Orders
        ORDER BY substr(StartDate, 1, 10), Position, Id
    """).fetchall()

    return {
        "status": "ok",
        "machines": [dict(machine) for machine in machines],
        "orders": [dict(order) for order in orders]
    }