import sqlite3
from conftest import TEST_DB
from validators import validate_activity_edit_form


def get_conn():
    conn = sqlite3.connect(TEST_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def test_edit_validate_ok_when_no_conflicts(client):
    db = get_conn()

    errors = validate_activity_edit_form(
        start="10:00",
        end="11:00",
        day_of_week=1,
        person_id=1,
        activity_id=999,  # nie istnieje – brak konfliktu
        db=db,
    )

    assert errors == []
    db.close()


def test_edit_validate_fails_when_start_after_end(client):
    db = get_conn()

    errors = validate_activity_edit_form(
        start="12:00",
        end="11:00",
        day_of_week=1,
        person_id=1,
        activity_id=1,
        db=db,
    )

    assert errors
    assert any("Start" in e or "wcześniejszy" in e for e in errors)
    db.close()


def test_edit_validate_fails_when_same_start_and_end(client):
    db = get_conn()

    errors = validate_activity_edit_form(
        start="11:00",
        end="11:00",
        day_of_week=1,
        person_id=1,
        activity_id=1,
        db=db,
    )

    assert errors
    assert any("Start" in e or "koniec" in e for e in errors)
    db.close()


def test_edit_validate_fails_on_time_conflict(client):
    db = get_conn()
    cur = db.cursor()

    # istniejąca aktywność (inna niż edytowana)
    cur.execute("""
        INSERT INTO ActiviesDays (
            DayOfWeek, StartTime, EndTime,
            ModelPersonFamilyId, ModelPictureActivityId
        )
        VALUES (1, '10:00', '11:00', 1, 1)
    """)
    db.commit()

    errors = validate_activity_edit_form(
        start="10:30",
        end="11:30",
        day_of_week=1,
        person_id=1,
        activity_id=999,  # edytujemy inną pozycję → konflikt ma być wykryty
        db=db,
    )

    assert errors
    assert any("zaplanowaną" in e or "koliz" in e.lower() for e in errors)
    db.close()


def test_edit_validate_ignores_self_conflict(client):
    db = get_conn()
    cur = db.cursor()

    # aktywność, którą będziemy "edytować"
    cur.execute("""
        INSERT INTO ActiviesDays (
            DayOfWeek, StartTime, EndTime,
            ModelPersonFamilyId, ModelPictureActivityId
        )
        VALUES (1, '10:00', '11:00', 1, 1)
    """)
    activity_id = cur.lastrowid
    db.commit()

    # te same godziny – ale to ta sama aktywność, więc ma przejść
    errors = validate_activity_edit_form(
        start="10:00",
        end="11:00",
        day_of_week=1,
        person_id=1,
        activity_id=activity_id,
        db=db,
    )

    assert errors == []
    db.close()
