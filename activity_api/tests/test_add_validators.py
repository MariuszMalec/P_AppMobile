import sqlite3

from conftest import TEST_DB
from validators import validate_activity_form


def get_conn():
    conn = sqlite3.connect(TEST_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def test_validate_ok_when_no_conflicts(client):
    # client uruchamia conftest i przygotowuje bazę
    db = get_conn()

    errors, picture_id = validate_activity_form(
        start="10:00",
        end="11:00",
        day_of_week=1,
        person_id=1,
        activity_name="Test",  # taka aktywność istnieje z insert_picture_activities
        db=db,
    )

    assert errors == []
    assert picture_id is not None

    db.close()


def test_validate_fails_when_start_after_end(client):
    db = get_conn()

    errors, picture_id = validate_activity_form(
        start="12:00",
        end="11:00",
        day_of_week=1,
        person_id=1,
        activity_name="Test",
        db=db,
    )

    assert errors
    assert picture_id is None

    db.close()


def test_validate_fails_when_start_thesame_end(client):
    db = get_conn()

    errors, picture_id = validate_activity_form(
        start="11:00",
        end="11:00",
        day_of_week=1,
        person_id=1,
        activity_name="Test",
        db=db,
    )

    assert errors
    assert any("nie mogą być takie same" in e for e in errors)
    assert picture_id is None

    db.close()


def test_validate_fails_on_time_conflict(client):
    db = get_conn()
    cur = db.cursor()

    # wstawiamy istniejącą aktywność
    cur.execute("""
        INSERT INTO ActiviesDays (
            DayOfWeek, StartTime, EndTime,
            ModelPersonFamilyId, ModelPictureActivityId
        )
        VALUES (1, '10:00', '11:00', 1, 1)
    """)
    db.commit()

    errors, picture_id = validate_activity_form(
        start="10:30",
        end="11:30",
        day_of_week=1,
        person_id=1,
        activity_name="Test",
        db=db,
    )

    assert errors
    assert any("zaplanowaną" in e or "koliz" in e.lower() for e in errors)
    assert picture_id is None

    db.close()
