from datetime import datetime
import re

TIME_RE = re.compile(r"^\d{2}:\d{2}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# =========================================================
# CZAS
# =========================================================

def hhmm(t: str) -> str:
    """
    Normalizuje czas do HH:MM.
    Obsługuje:
        HH:MM
        HH:MM:SS
    """
    if t is None:
        raise ValueError("Godzina jest wymagana")

    t = str(t).strip()

    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(t, fmt).strftime("%H:%M")
        except ValueError:
            pass

    raise ValueError(
        f"Nieobsługiwany format czasu: {t}"
    )


def time_to_minutes(t: str) -> int:
    """
    Zamienia HH:MM na liczbę minut od północy.
    """
    t = hhmm(t)
    hours, minutes = map(int, t.split(":"))
    return hours * 60 + minutes


def validate_time_range(start: str, end: str) -> tuple[str, str]:
    """
    Sprawdza poprawność zakresu czasu.

    Zwraca znormalizowane:
        start, end
    """
    if not start or not end:
        raise ValueError(
            "Godzina rozpoczęcia i zakończenia są wymagane"
        )

    start = hhmm(start)
    end = hhmm(end)

    start_minutes = time_to_minutes(start)
    end_minutes = time_to_minutes(end)

    if start_minutes >= end_minutes:
        raise ValueError(
            "Godzina zakończenia musi być późniejsza niż rozpoczęcia"
        )

    return start, end


# =========================================================
# KONFLIKT CZASOWY
# =========================================================

def ranges_overlap(
    start1: int,
    end1: int,
    start2: int,
    end2: int
) -> bool:
    """
    Zwraca True, jeżeli dwa zakresy czasu nachodzą na siebie.

    Przykłady:
        16:00-17:00
        16:30-17:30  -> True

        16:00-17:00
        17:00-18:00  -> False
    """
    return start1 < end2 and start2 < end1


def find_time_conflict(
    start: str,
    end: str,
    existing_sessions,
    exclude_session_id: int | None = None
):
    """
    Szuka konfliktu czasowego wśród istniejących sesji.

    existing_sessions musi zawierać:
        Id
        StartTime
        EndTime

    Zwraca konfliktującą sesję albo None.
    """

    start_minutes = time_to_minutes(start)
    end_minutes = time_to_minutes(end)

    for session in existing_sessions:

        # Przy edycji pomijamy edytowaną sesję
        if (
            exclude_session_id is not None
            and session["Id"] == exclude_session_id
        ):
            continue

        try:
            other_start_minutes = time_to_minutes(
                session["StartTime"]
            )

            other_end_minutes = time_to_minutes(
                session["EndTime"]
            )

        except (ValueError, TypeError, KeyError):
            # Uszkodzone dane w bazie nie powodują
            # błędu całego requestu
            continue

        if ranges_overlap(
            start_minutes,
            end_minutes,
            other_start_minutes,
            other_end_minutes
        ):
            return session

    return None


# =========================================================
# DZIEŃ TYGODNIA
# =========================================================

def validate_day_of_week(day_of_week: int) -> int:
    """
    Sprawdza dzień tygodnia:
        1 = poniedziałek
        ...
        7 = niedziela
    """

    try:
        day_of_week = int(day_of_week)
    except (ValueError, TypeError):
        raise ValueError(
            "Nieprawidłowy dzień tygodnia"
        )

    if day_of_week < 1 or day_of_week > 7:
        raise ValueError(
            "Nieprawidłowy dzień tygodnia"
        )

    return day_of_week


# =========================================================
# DATA SESJI
# =========================================================

def validate_session_date(session_date: str) -> str:
    """
    Sprawdza datę sesji w formacie YYYY-MM-DD.
    """

    if not session_date:
        raise ValueError(
            "Data sesji jest wymagana"
        )

    session_date = str(session_date).strip()

    if not DATE_RE.match(session_date):
        raise ValueError(
            "Nieprawidłowy format daty sesji"
        )

    try:
        datetime.strptime(
            session_date,
            "%Y-%m-%d"
        )
    except ValueError:
        raise ValueError(
            "Nieprawidłowa data sesji"
        )

    return session_date


# =========================================================
# PEŁNA WALIDACJA SESJI
# =========================================================

def validate_session_data(
    start: str,
    end: str,
    day_of_week: int,
    session_date: str
) -> tuple[str, str, int, str]:
    """
    Wspólna walidacja danych sesji.

    Zwraca:
        start,
        end,
        day_of_week,
        session_date
    """

    start, end = validate_time_range(
        start,
        end
    )

    day_of_week = validate_day_of_week(
        day_of_week
    )

    session_date = validate_session_date(
        session_date
    )

    return (
        start,
        end,
        day_of_week,
        session_date
    )


# =========================================================
# KLIENT
# =========================================================

def validate_client_id(client_id: int) -> int:
    """
    Sprawdza podstawową poprawność ID klienta.
    Sprawdzenie czy klient faktycznie istnieje
    pozostaje w backendzie, ponieważ wymaga bazy.
    """

    try:
        client_id = int(client_id)
    except (ValueError, TypeError):
        raise ValueError(
            "Nieprawidłowy klient"
        )

    if client_id <= 0:
        raise ValueError(
            "Nieprawidłowy klient"
        )

    return client_id


# =========================================================
# KLIENT - DANE
# =========================================================

def validate_client_data(
    first_name: str,
    last_name: str,
    age=None,
    phone: str = "",
    gender: str = "",
    description: str = ""
):
    """
    Walidacja danych nowego klienta.
    """

    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()

    if not first_name or not last_name:
        raise ValueError(
            "Imię i nazwisko są wymagane"
        )

    if age is not None:
        try:
            age = int(age)
        except (ValueError, TypeError):
            raise ValueError(
                "Wiek musi być liczbą"
            )

        if age < 0:
            raise ValueError(
                "Wiek nie może być ujemny"
            )

    return {
        "first_name": first_name,
        "last_name": last_name,
        "age": age,
        "phone": (phone or "").strip(),
        "gender": (gender or "").strip(),
        "description": (description or "").strip()
    }
