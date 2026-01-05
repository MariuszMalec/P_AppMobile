from datetime import datetime
import re
from enums import DAY_NAMES, PERSON_ENUM_MAP


TIME_RE = re.compile(r"^\d{2}:\d{2}$")

def time_to_minutes(value: str) -> int:
    t = datetime.strptime(value, "%H:%M")
    return t.hour * 60 + t.minute

def validate_activity_form(
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


        print(start_min)
        print(end_min)

        # ✅ TU JEST WŁAŚCIWA WALIDACJA
        if not errors and start_min >= end_min:
            errors.append("Godzina startu musi być wcześniejsza niż zakończenia")


    # --- dzień ---
    if day_of_week not in DAY_NAMES or day_of_week == 0:
        errors.append("Nieprawidłowy dzień tygodnia")

    # --- enumy ---
    if person_id not in PERSON_ENUM_MAP:
        errors.append("Nieprawidłowa osoba")

    if picture_name is None:
        errors.append("Nieprawidłowa aktywność")

    return errors

def validate_activity_edit_form(
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


        print(start_min)
        print(end_min)

        # ✅ TU JEST WŁAŚCIWA WALIDACJA
        if not errors and start_min >= end_min:
            errors.append("Godzina startu musi być wcześniejsza niż zakończenia")


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
