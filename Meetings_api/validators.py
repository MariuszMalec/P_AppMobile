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


def time_to_minutes(t: str) -> int:
    t = hhmm(t)
    hours, minutes = map(int, t.split(":"))
    return hours * 60 + minutes


def ranges_overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
    return start1 < end2 and start2 < end1