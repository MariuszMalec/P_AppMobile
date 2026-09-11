import sqlite3

import pytest

from conftest import TEST_DB
from validators import (
    validate_session_data,
    find_time_conflict,
    validate_client_id,
)


def get_conn():
    conn = sqlite3.connect(TEST_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def test_validate_session_ok():
    start, end, day_of_week, session_date = validate_session_data(
        start="10:00",
        end="11:00",
        day_of_week=1,
        session_date="2026-09-07",
    )

    assert start == "10:00"
    assert end == "11:00"
    assert day_of_week == 1
    assert session_date == "2026-09-07"


def test_validate_session_fails_when_start_after_end():
    with pytest.raises(
        ValueError,
        match="Godzina zakończenia musi być późniejsza niż rozpoczęcia"
    ):
        validate_session_data(
            start="12:00",
            end="11:00",
            day_of_week=1,
            session_date="2026-09-07",
        )


def test_validate_session_fails_when_start_equals_end():
    with pytest.raises(
        ValueError,
        match="Godzina zakończenia musi być późniejsza niż rozpoczęcia"
    ):
        validate_session_data(
            start="11:00",
            end="11:00",
            day_of_week=1,
            session_date="2026-09-07",
        )


def test_validate_session_fails_on_invalid_day():
    with pytest.raises(
        ValueError,
        match="Nieprawidłowy dzień tygodnia"
    ):
        validate_session_data(
            start="10:00",
            end="11:00",
            day_of_week=8,
            session_date="2026-09-07",
        )


def test_validate_session_fails_on_invalid_date():
    with pytest.raises(
        ValueError,
        match="Nieprawidłowa"
    ):
        validate_session_data(
            start="10:00",
            end="11:00",
            day_of_week=1,
            session_date="2026-99-99",
        )


def test_find_time_conflict():
    existing_sessions = [
        {
            "Id": 1,
            "StartTime": "10:00",
            "EndTime": "11:00",
        }
    ]

    conflict = find_time_conflict(
        start="10:30",
        end="11:30",
        existing_sessions=existing_sessions,
    )

    assert conflict is not None
    assert conflict["Id"] == 1


def test_find_time_conflict_returns_none_when_no_conflict():
    existing_sessions = [
        {
            "Id": 1,
            "StartTime": "10:00",
            "EndTime": "11:00",
        }
    ]

    conflict = find_time_conflict(
        start="11:00",
        end="12:00",
        existing_sessions=existing_sessions,
    )

    assert conflict is None


def test_find_time_conflict_ignores_current_session():
    existing_sessions = [
        {
            "Id": 5,
            "StartTime": "10:00",
            "EndTime": "11:00",
        }
    ]

    conflict = find_time_conflict(
        start="10:00",
        end="11:00",
        existing_sessions=existing_sessions,
        exclude_session_id=5,
    )

    assert conflict is None


def test_validate_client_id_ok():
    assert validate_client_id(1) == 1
    assert validate_client_id("2") == 2


def test_validate_client_id_fails_for_invalid_id():
    with pytest.raises(
        ValueError,
        match="Nieprawidłowy klient"
    ):
        validate_client_id(0)
