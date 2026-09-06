from datetime import datetime
import re
from enums import DAY_NAMES, PERSON_ENUM_MAP


TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def hhmm(t: str) -> str:
    t = t.strip()

    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(t, fmt).strftime("%H:%M")
        except ValueError:
            pass

    raise ValueError(f"Nieobsługiwany format czasu: {t}")


def time_to_minutes(value: str) -> int:
    value = value.strip()

    if len(value) == 5:      # HH:MM
        h, m = value.split(":")
    else:                    # HH:MM:SS
        h, m, _ = value.split(":")

    return int(h) * 60 + int(m)


def validate_activity_form(
    start: str,
    end: str,
    day_of_week: int,
    person_id: int,
    activity_name: str,
    db,
):
    errors = []
    cursor = db.cursor()

    # --- format czasu ---
    try:
        start_min = time_to_minutes(start)
        end_min   = time_to_minutes(end)
    except Exception:
        errors.append("Nieprawidłowy format czasu")
        return errors, None

    if start_min == end_min:
        errors.append("Godzina rozpoczęcia i zakończenia nie mogą być takie same")

    if day_of_week not in range(1, 8):
        errors.append("Nieprawidłowy dzień tygodnia")

    # --- aktywność ---
    cursor.execute(
        "SELECT Id FROM PictureActivities WHERE Name = ?",
        (activity_name,)
    )
    row = cursor.fetchone()

    if not row:
        errors.append("Nieprawidłowa aktywność")
        return errors, None

    picture_id = row["Id"]

    # --- kolizje ---
    cursor.execute("""
        SELECT StartTime, EndTime
        FROM ActiviesDays
        WHERE
            DayOfWeek = ?
            AND ModelPersonFamilyId = ?
    """, (
        day_of_week,
        5 if person_id == 0 else person_id
    ))

    existing = cursor.fetchall()
    new_ranges = normalize_range(start_min, end_min)

    for row in existing:
        ex_start = time_to_minutes(row["StartTime"])
        ex_end   = time_to_minutes(row["EndTime"])
        ex_ranges = normalize_range(ex_start, ex_end)

        for nr in new_ranges:
            for er in ex_ranges:
                if ranges_overlap(nr, er):
                    errors.append(
                        f"❌ Masz już zaplanowaną aktywność w tym czasie "
                        f"({row['StartTime']} – {row['EndTime']})"
                    )
                    return errors, None

    return errors, picture_id



def validate_activity_edit_form(
    start: str,
    end: str,
    day_of_week: int,
    person_id: int,
    activity_id: int,
    db,
):
    errors: list[str] = []

    # --- walidacja podstawowa czasu ---
    try:
        start_min = time_to_minutes(start)
        end_min = time_to_minutes(end)
    except Exception:
        errors.append("Nieprawidłowy format czasu")
        return errors

    if start_min == end_min:
        errors.append("Godzina rozpoczęcia i zakończenia nie mogą być takie same")

    # jeżeli są już błędy – nie ma sensu iść do bazy
    if errors:
        return errors

    cursor = db.cursor()

    # --- pobieramy inne aktywności (bez tej edytowanej) ---
    cursor.execute("""
        SELECT StartTime, EndTime
        FROM ActiviesDays
        WHERE
            DayOfWeek = ?
            AND ModelPersonFamilyId = ?
            AND Id != ?
    """, (day_of_week, person_id, activity_id))

    existing = cursor.fetchall()

    new_ranges = normalize_range(start_min, end_min)

    for row in existing:
        ex_start = time_to_minutes(row["StartTime"])
        ex_end = time_to_minutes(row["EndTime"])

        ex_ranges = normalize_range(ex_start, ex_end)

        for nr in new_ranges:
            for er in ex_ranges:
                if ranges_overlap(nr, er):
                    errors.append(
                        f"❌ Masz już zaplanowaną aktywność w tym czasie "
                        f"({row['StartTime']} – {row['EndTime']})"
                    )
                    return errors  # jedna kolizja wystarczy

    return errors



def validate_activity_form_old(
    start: str,
    end: str,
    day_of_week: int,
    person_id: int,
    picture_name: str
) -> list[str]:
    errors = []

    # --- czas ---
    if not TIME_RE.match(start):
        errors.append("StartTime musi być w formacie HH:MM")

    if not TIME_RE.match(end):
        errors.append("EndTime musi być w formacie HH:MM")

    if TIME_RE.match(start) and TIME_RE.match(end):

        try:
            start_min = time_to_minutes(start)
            end_min = time_to_minutes(end)
        except ValueError as e:
            errors.append(str(e))

        # ✅ TU JEST WŁAŚCIWA WALIDACJA
        if not errors and start_min == end_min:
            errors.append("Godzina startu musi być inna niż zakończenia")

    # --- dzień ---
    if day_of_week not in DAY_NAMES or day_of_week == 0:
        errors.append("Nieprawidłowy dzień tygodnia")

    # --- enumy ---
    if person_id not in PERSON_ENUM_MAP:
        errors.append("Nieprawidłowa osoba")

    if picture_name is None:
        errors.append("Nieprawidłowa aktywność")

    return errors

def validate_activity_edit_form_old(
    start: str,
    end: str,
    day_of_week: int,
    person_id: int,
) -> list[str]:
    errors = []

    # --- czas ---
    if not TIME_RE.match(start):
        errors.append("StartTime musi być w formacie HH:MM")

    if not TIME_RE.match(end):
        errors.append("EndTime musi być w formacie HH:MM")

    if TIME_RE.match(start) and TIME_RE.match(end):

        try:
            start_min = time_to_minutes(start)
            end_min = time_to_minutes(end)
        except ValueError as e:
            errors.append(str(e))

        # ❌ tylko gdy start jest PO end
        if start_min > end_min:
            errors.append("❌ Godzina rozpoczęcia musi być wcześniejsza niż zakończenia")

        # ❌ opcjonalnie: blokada zerowej aktywności
        if start_min == end_min:
            errors.append("❌ Czas trwania aktywności nie może wynosić 0 minut")

    # --- dzień ---
    if day_of_week not in DAY_NAMES or day_of_week == 0:
        errors.append("Nieprawidłowy dzień tygodnia")

    # --- enumy ---
    if person_id not in PERSON_ENUM_MAP:
        errors.append("Nieprawidłowa osoba")


    return errors

def system_day_to_db_day(iso_day: int) -> int:
    # iso: 1=Mon ... 7=Sun
    # db : 1=Sun ... 7=Sat
    return 1 if iso_day == 7 else iso_day + 1

def normalize_range(start_min: int, end_min: int) -> list[tuple[int, int]]:
    if end_min > start_min:
        return [(start_min, end_min)]
    return [
        (start_min, 1440),
        (0, end_min)
    ]

def ranges_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]