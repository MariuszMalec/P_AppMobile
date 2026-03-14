from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import HTMLResponse, JSONResponse
from templates import templates
from db import get_db
from collections import defaultdict
from datetime import datetime, timedelta
import calendar
import hashlib

router = APIRouter(
    prefix="/shifts",
    tags=["shifts"]
)

# =====================================================
# GŁÓWNA STRONA SHIFTS
# =====================================================
@router.get("/", response_class=HTMLResponse)
def shift_page(request: Request, db=Depends(get_db)):
    cursor = db.cursor()

    # =============================
    # Pobranie pracowników
    # =============================
    employees = cursor.execute("""
        SELECT 
            Id,
            FirstName,
            LastName,
            Color
        FROM Employees
        ORDER BY Id
    """).fetchall()

    # =============================
    # Pobranie wszystkich WorkShifts
    # =============================
    workshifts = cursor.execute("SELECT * FROM WorkShifts ORDER BY Id").fetchall()

    # =============================
    # Aktualny miesiąc
    # =============================
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    num_days = calendar.monthrange(current_year, current_month)[1]

    first_day = f"{current_year}-{current_month:02d}-01"
    last_day = f"{current_year}-{current_month:02d}-{num_days:02d}"

    # =============================
    # Pobranie grafiku na miesiąc
    # =============================
    shifts = cursor.execute("""
        SELECT 
            es.EmployeeId,
            es.WorkShiftId,
            es.ShiftDate,
            ws.Name as ShiftName,
            ws.Description as ShiftDescription,
            ws.Picture as ShiftPicture
        FROM EmployeeShifts es
        JOIN WorkShifts ws ON ws.Id = es.WorkShiftId
        WHERE es.ShiftDate BETWEEN ? AND ?
    """, (first_day, last_day)).fetchall()

    # =============================
    # Budowanie struktury schedule
    # =============================
    schedule = defaultdict(dict)

    for s in shifts:
        date_key = s["ShiftDate"][:10]
        schedule[s["EmployeeId"]][date_key] = {
            "WorkShiftId": s["WorkShiftId"],
            "ShiftName": s["ShiftName"],
            "ShiftDescription": s["ShiftDescription"],
            "ShiftPicture": s["ShiftPicture"]
        }

    # =============================
    # Lista dni miesiąca
    # =============================
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
        "shifts.html",
        {
            "request": request,
            "employees": employees,
            "days": days,
            "schedule": schedule,
            "workshifts": workshifts
        }
    )


# =====================================================
# Ustawienie zmiany dla pracownika
# =====================================================
@router.post("/set")
def set_shift(
    data: dict = Body(...),
    db=Depends(get_db)
):
    """
    data = {
        "EmployeeId": 1,
        "WorkShiftId": 2,
        "ShiftDate": "2026-02-14",
        "Days": 3
    }
    """
    from datetime import datetime, timedelta

    try:
        cursor = db.cursor()

        employee_id = int(data["EmployeeId"])
        workshift_id = int(data["WorkShiftId"])
        start_date = datetime.strptime(data["ShiftDate"], "%Y-%m-%d")
        days = int(data.get("Days", 1))

        added = 0
        current_date = start_date

        while added < days:
            # Sprawdź czy jest już zmiana dla tego pracownika
            exists = cursor.execute(
                "SELECT 1 FROM EmployeeShifts WHERE EmployeeId=? AND ShiftDate=?",
                (employee_id, current_date.strftime("%Y-%m-%d"))
            ).fetchone()

            if not exists:
                # Dodajemy zmianę
                cursor.execute(
                    "INSERT INTO EmployeeShifts (EmployeeId, WorkShiftId, ShiftDate) VALUES (?, ?, ?)",
                    (employee_id, workshift_id, current_date.strftime("%Y-%m-%d"))
                )
                db.commit()
                added += 1

            # Idziemy do kolejnego dnia
            current_date += timedelta(days=1)

        return JSONResponse({"status": "ok"})

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})



# =====================================================
# Usunięcie zmiany dla pracownika
# =====================================================
@router.post("/delete")
def delete_shift(payload: dict, db=Depends(get_db)):
    """
    payload = {
        "EmployeeId": int,
        "ShiftDate": "YYYY-MM-DD"
    }
    """
    cursor = db.cursor()
    try:
        cursor.execute("""
            DELETE FROM EmployeeShifts
            WHERE EmployeeId = ? AND ShiftDate = ?
        """, (payload["EmployeeId"], payload["ShiftDate"]))

        db.commit()
        return JSONResponse({"status": "ok"})
    except Exception as e:
        db.rollback()
        return JSONResponse({"status": "error", "message": str(e)})


# =====================================================
# USUNIĘCIE WSZYSTKICH ZMIAN
# =====================================================
@router.post("/delete_all")
def delete_all_shifts(db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM EmployeeShifts")
        db.commit()
        return JSONResponse({
            "status": "ok",
            "message": "Wszystkie zmiany zostały usunięte"
        })
    except Exception as e:
        db.rollback()
        return JSONResponse({
            "status": "error",
            "message": str(e)
        })
    

@router.post("/auto_fill")
def auto_fill_shifts(db=Depends(get_db)):

    cursor = db.cursor()

    try:
        # =============================
        # Pobranie pracowników
        # =============================
        employees = cursor.execute("""
            SELECT Id FROM Employees ORDER BY Id
        """).fetchall()

        if not employees:
            return JSONResponse({
                "status": "error",
                "message": "Brak pracowników"
            })

        employee_ids = [e["Id"] for e in employees]

        # =============================
        # Bieżący miesiąc (tak jak w shift_page)
        # =============================
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        num_days = calendar.monthrange(current_year, current_month)[1]

        start_date = datetime(current_year, current_month, 1)
        end_date = datetime(current_year, current_month, num_days)

        # =============================
        # Usuwamy zmiany z tego miesiąca
        # =============================
        cursor.execute("""
            DELETE FROM EmployeeShifts
            WHERE ShiftDate BETWEEN ? AND ?
        """, (
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        ))

        # =============================
        # Generowanie grafiku
        # =============================
        current_date = start_date
        week_index = -1
        current_week = None

        while current_date <= end_date:

            # ⛔ pomijamy weekend
            if current_date.weekday() < 5:

                week_number = current_date.isocalendar()[1]

                if week_number != current_week:
                    current_week = week_number
                    week_index += 1

                second_shift_index = week_index % len(employee_ids)

                for idx, emp_id in enumerate(employee_ids):

                    work_shift_id = 2 if idx == second_shift_index else 1

                    cursor.execute("""
                        INSERT INTO EmployeeShifts (EmployeeId, WorkShiftId, ShiftDate)
                        VALUES (?, ?, ?)
                    """, (
                        emp_id,
                        work_shift_id,
                        current_date.strftime("%Y-%m-%d")
                    ))

            current_date += timedelta(days=1)

        db.commit()

        return JSONResponse({
            "status": "ok",
            "message": "Grafik wygenerowany poprawnie"
        })

    except Exception as e:
        db.rollback()
        return JSONResponse({
            "status": "error",
            "message": str(e)
        })



# =====================================================
# AKTUALIZACJA ZMIANY (UPDATE)
# =====================================================
@router.post("/update")
def update_shift(
    data: dict = Body(...),
    db=Depends(get_db)
):

    try:
        cursor = db.cursor()

        employee_id = int(data["EmployeeId"])
        workshift_id = int(data["WorkShiftId"])
        start_date = datetime.strptime(data["ShiftDate"], "%Y-%m-%d")
        days = int(data.get("Days", 1))

        added_days = 0
        current_date = start_date

        while added_days < days:

            # pomiń weekend
            if current_date.weekday() < 5:

                shift_date_str = current_date.strftime("%Y-%m-%d")

                exists = cursor.execute("""
                    SELECT 1 FROM EmployeeShifts
                    WHERE EmployeeId = ? AND ShiftDate = ?
                """, (employee_id, shift_date_str)).fetchone()

                if exists:
                    cursor.execute("""
                        UPDATE EmployeeShifts
                        SET WorkShiftId = ?
                        WHERE EmployeeId = ? AND ShiftDate = ?
                    """, (workshift_id, employee_id, shift_date_str))
                else:
                    cursor.execute("""
                        INSERT INTO EmployeeShifts (EmployeeId, WorkShiftId, ShiftDate)
                        VALUES (?, ?, ?)
                    """, (employee_id, workshift_id, shift_date_str))

                added_days += 1

            current_date += timedelta(days=1)

        db.commit()

        return JSONResponse({"status": "ok"})

    except Exception as e:
        db.rollback()
        return JSONResponse({
            "status": "error",
            "message": str(e)
        })