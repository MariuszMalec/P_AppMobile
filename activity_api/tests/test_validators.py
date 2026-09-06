import sqlite3
import pytest

from conftest import TEST_DB

from validators import (
    hhmm,
    time_to_minutes,
    normalize_range,
    ranges_overlap,
    system_day_to_db_day,
    validate_activity_form,
    validate_activity_edit_form,
)


# ============================================================
# Pomocnicze funkcje
# ============================================================

def get_test_db():
    db = sqlite3.connect(
        TEST_DB,
        check_same_thread=False
    )
    db.row_factory = sqlite3.Row
    return db


def add_person(db, person_id=1):
    db.execute(
        """
        INSERT INTO PersonFamilies (
            Id,
            PersonName,
            PersonPicture
        )
        VALUES (?, ?, ?)
        """,
        (
            person_id,
            f"TEST_PERSON_{person_id}",
            ""
        )
    )
    db.commit()


def add_activity(db, activity_id=1, name="Testowa"):
    db.execute(
        """
        INSERT INTO PictureActivities (
            Id,
            ActivityName,
            Name,
            Picture
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            activity_id,
            activity_id,
            name,
            ""
        )
    )
    db.commit()


def add_session(
    db,
    start="10:00:00",
    end="11:00:00",
    day_of_week=1,
    person_id=1,
    activity_id=1,
):
    cursor = db.execute(
        """
        INSERT INTO ActiviesDays (
            StartTime,
            EndTime,
            Description,
            DayOfWeek,
            ModelPersonFamilyId,
            ModelPictureActivityId
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            start,
            end,
            "Test",
            day_of_week,
            person_id,
            activity_id,
        )
    )

    db.commit()

    return cursor.lastrowid


# ============================================================
# hhmm
# ============================================================

def test_hhmm_hhmm():
    assert hhmm("10:30") == "10:30"


def test_hhmm_hhmmss():
    assert hhmm("10:30:45") == "10:30"


def test_hhmm_invalid():
    with pytest.raises(ValueError):
        hhmm("abc")


def test_hhmm_invalid_hour():
    with pytest.raises(ValueError):
        hhmm("25:00")


# ============================================================
# time_to_minutes
# ============================================================

def test_time_to_minutes_hhmm():
    assert time_to_minutes("10:30") == 630


def test_time_to_minutes_hhmmss():
    assert time_to_minutes("10:30:45") == 630


def test_time_to_minutes_midnight():
    assert time_to_minutes("00:00") == 0


def test_time_to_minutes_end_of_day():
    assert time_to_minutes("23:59") == 1439


# ============================================================
# normalize_range
# ============================================================

def test_normalize_range_normal():
    assert normalize_range(600, 660) == [
        (600, 660)
    ]


def test_normalize_range_crosses_midnight():
    assert normalize_range(1380, 60) == [
        (1380, 1440),
        (0, 60)
    ]


def test_normalize_range_same_time():
    assert normalize_range(600, 600) == [
        (600, 1440),
        (0, 600)
    ]


# ============================================================
# ranges_overlap
# ============================================================

def test_ranges_overlap_true():
    assert ranges_overlap(
        (600, 660),
        (630, 690)
    ) is True


def test_ranges_overlap_false():
    assert ranges_overlap(
        (600, 660),
        (660, 720)
    ) is False


def test_ranges_overlap_inside():
    assert ranges_overlap(
        (600, 720),
        (630, 660)
    ) is True


# ============================================================
# system_day_to_db_day
# ============================================================

@pytest.mark.parametrize(
    "iso_day, expected",
    [
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 1),
    ]
)
def test_system_day_to_db_day(iso_day, expected):
    assert system_day_to_db_day(iso_day) == expected


# ============================================================
# validate_activity_form
# ============================================================

def test_validate_activity_form_ok(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        errors, picture_id = validate_activity_form(
            start="10:00",
            end="11:00",
            day_of_week=1,
            person_id=1,
            activity_name="Testowa",
            db=db,
        )

        assert errors == []
        assert picture_id == 1

    finally:
        db.close()


def test_validate_activity_form_same_time(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        errors, picture_id = validate_activity_form(
            start="10:00",
            end="10:00",
            day_of_week=1,
            person_id=1,
            activity_name="Testowa",
            db=db,
        )

        assert "Godzina rozpoczęcia i zakończenia nie mogą być takie same" in errors
        assert picture_id == 1

    finally:
        db.close()


def test_validate_activity_form_invalid_time(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        errors, picture_id = validate_activity_form(
            start="abc",
            end="11:00",
            day_of_week=1,
            person_id=1,
            activity_name="Testowa",
            db=db,
        )

        assert errors == ["Nieprawidłowy format czasu"]
        assert picture_id is None

    finally:
        db.close()


def test_validate_activity_form_invalid_day(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        errors, picture_id = validate_activity_form(
            start="10:00",
            end="11:00",
            day_of_week=8,
            person_id=1,
            activity_name="Testowa",
            db=db,
        )

        assert "Nieprawidłowy dzień tygodnia" in errors
        assert picture_id == 1

    finally:
        db.close()


def test_validate_activity_form_invalid_activity(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)

        errors, picture_id = validate_activity_form(
            start="10:00",
            end="11:00",
            day_of_week=1,
            person_id=1,
            activity_name="Nieistniejaca",
            db=db,
        )

        assert "Nieprawidłowa aktywność" in errors
        assert picture_id is None

    finally:
        db.close()


def test_validate_activity_form_conflict(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        add_session(
            db,
            start="10:00:00",
            end="11:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        errors, picture_id = validate_activity_form(
            start="10:30",
            end="11:30",
            day_of_week=1,
            person_id=1,
            activity_name="Testowa",
            db=db,
        )

        assert len(errors) == 1
        assert "Masz już zaplanowaną aktywność w tym czasie" in errors[0]
        assert picture_id is None

    finally:
        db.close()


def test_validate_activity_form_adjacent_time_ok(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        add_session(
            db,
            start="10:00:00",
            end="11:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        errors, picture_id = validate_activity_form(
            start="11:00",
            end="12:00",
            day_of_week=1,
            person_id=1,
            activity_name="Testowa",
            db=db,
        )

        assert errors == []
        assert picture_id == 1

    finally:
        db.close()


def test_validate_activity_form_different_person_ok(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_person(db, 2)
        add_activity(db, 1, "Testowa")

        add_session(
            db,
            start="10:00:00",
            end="11:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        errors, picture_id = validate_activity_form(
            start="10:30",
            end="11:30",
            day_of_week=1,
            person_id=2,
            activity_name="Testowa",
            db=db,
        )

        assert errors == []
        assert picture_id == 1

    finally:
        db.close()


def test_validate_activity_form_family_person_zero_uses_id_5(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 5)
        add_activity(db, 1, "Testowa")

        add_session(
            db,
            start="10:00:00",
            end="11:00:00",
            day_of_week=1,
            person_id=5,
            activity_id=1,
        )

        errors, picture_id = validate_activity_form(
            start="10:30",
            end="11:30",
            day_of_week=1,
            person_id=0,
            activity_name="Testowa",
            db=db,
        )

        assert len(errors) == 1
        assert "Masz już zaplanowaną aktywność w tym czasie" in errors[0]
        assert picture_id is None

    finally:
        db.close()


# ============================================================
# validate_activity_edit_form
# ============================================================

def test_validate_activity_edit_form_ok(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        session_id = add_session(
            db,
            start="10:00:00",
            end="11:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        errors = validate_activity_edit_form(
            start="12:00",
            end="13:00",
            day_of_week=1,
            person_id=1,
            activity_id=session_id,
            db=db,
        )

        assert errors == []

    finally:
        db.close()


def test_validate_activity_edit_form_same_time(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        session_id = add_session(
            db,
            start="10:00:00",
            end="11:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        errors = validate_activity_edit_form(
            start="10:00",
            end="10:00",
            day_of_week=1,
            person_id=1,
            activity_id=session_id,
            db=db,
        )

        assert "Godzina rozpoczęcia i zakończenia nie mogą być takie same" in errors

    finally:
        db.close()


def test_validate_activity_edit_form_invalid_time(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        session_id = add_session(
            db,
            start="10:00:00",
            end="11:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        errors = validate_activity_edit_form(
            start="abc",
            end="11:00",
            day_of_week=1,
            person_id=1,
            activity_id=session_id,
            db=db,
        )

        assert errors == ["Nieprawidłowy format czasu"]

    finally:
        db.close()


def test_validate_activity_edit_form_conflict(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        session1_id = add_session(
            db,
            start="10:00:00",
            end="11:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        session2_id = add_session(
            db,
            start="12:00:00",
            end="13:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        errors = validate_activity_edit_form(
            start="10:30",
            end="11:30",
            day_of_week=1,
            person_id=1,
            activity_id=session2_id,
            db=db,
        )

        assert len(errors) == 1
        assert "Masz już zaplanowaną aktywność w tym czasie" in errors[0]

    finally:
        db.close()


def test_validate_activity_edit_form_same_session_not_conflict(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        session_id = add_session(
            db,
            start="10:00:00",
            end="11:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        errors = validate_activity_edit_form(
            start="10:30",
            end="11:30",
            day_of_week=1,
            person_id=1,
            activity_id=session_id,
            db=db,
        )

        assert errors == []

    finally:
        db.close()


def test_validate_activity_edit_form_adjacent_time_ok(client, empty_db):
    db = get_test_db()

    try:
        add_person(db, 1)
        add_activity(db, 1, "Testowa")

        add_session(
            db,
            start="10:00:00",
            end="11:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        session2_id = add_session(
            db,
            start="12:00:00",
            end="13:00:00",
            day_of_week=1,
            person_id=1,
            activity_id=1,
        )

        errors = validate_activity_edit_form(
            start="11:00",
            end="12:00",
            day_of_week=1,
            person_id=1,
            activity_id=session2_id,
            db=db,
        )

        assert errors == []

    finally:
        db.close()
