from datetime import datetime, timedelta

from db import DB_PATH
from conftest import TEST_DB


# ============================================================
# POMOCNICZE FUNKCJE
# ============================================================

def get_db():
    import sqlite3

    db = sqlite3.connect(TEST_DB, check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db


def get_monday():
    today = datetime.now().date()
    return today - timedelta(days=today.weekday())


def insert_client(
    first_name="Jan",
    last_name="Kowalski",
    age=30,
    description="",
    phone="123456789",
    gender="male"
):
    db = get_db()

    try:
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO Client (
                FirstName,
                LastName,
                Age,
                Description,
                Phone,
                Gender
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                first_name,
                last_name,
                age,
                description,
                phone,
                gender
            )
        )

        client_id = cursor.lastrowid
        db.commit()

        return client_id

    finally:
        db.close()


def insert_session(
    client_id,
    start="10:00",
    end="11:00",
    description="Test",
    day_of_week=1,
    session_date=None,
    recurring_group_id=None
):
    if session_date is None:
        session_date = get_monday().isoformat()

    db = get_db()

    try:
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO Session (
                StartTime,
                EndTime,
                ClientId,
                Description,
                DayOfWeek,
                SessionDate,
                RecurringGroupId
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                start,
                end,
                client_id,
                description,
                day_of_week,
                session_date,
                recurring_group_id
            )
        )

        session_id = cursor.lastrowid
        db.commit()

        return session_id

    finally:
        db.close()


# ============================================================
# HOME / SESSION
# ============================================================

def test_home_page_returns_200(client):
    response = client.get("/home/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


# ============================================================
# GET RECURRING COUNT
# ============================================================

def test_recurring_count(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    recurring_group_id = 123

    insert_session(
        client_id=client_id,
        session_date=monday.isoformat(),
        recurring_group_id=recurring_group_id
    )

    insert_session(
        client_id=client_id,
        session_date=(monday + timedelta(days=7)).isoformat(),
        recurring_group_id=recurring_group_id
    )

    response = client.get(
        f"/home/session/recurring-count/{recurring_group_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 2


# ============================================================
# CREATE SESSION
# ============================================================

def test_create_session_ok(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "11:00",
            "client_id": client_id,
            "description": "Testowa sesja",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "recurring": "false",
            "recurring_weeks": 1
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["created"] == 1
    assert data["recurring_group_id"] is None
    assert data["dates"] == [monday.isoformat()]

    db = get_db()

    try:
        row = db.execute(
            """
            SELECT *
            FROM Session
            WHERE Id = (
                SELECT MAX(Id)
                FROM Session
            )
            """
        ).fetchone()

        assert row is not None
        assert row["StartTime"] == "10:00"
        assert row["EndTime"] == "11:00"
        assert row["ClientId"] == client_id
        assert row["Description"] == "Testowa sesja"
        assert row["DayOfWeek"] == 1
        assert row["SessionDate"] == monday.isoformat()
        assert row["RecurringGroupId"] is None

    finally:
        db.close()


def test_create_recurring_session(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "11:00",
            "client_id": client_id,
            "description": "Seria",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "recurring": "true",
            "recurring_weeks": 3
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["created"] == 4
    assert data["recurring_group_id"] is not None

    expected_dates = [
        (monday + timedelta(days=i * 7)).isoformat()
        for i in range(4)
    ]

    assert data["dates"] == expected_dates

    db = get_db()

    try:
        rows = db.execute(
            """
            SELECT *
            FROM Session
            WHERE RecurringGroupId = ?
            ORDER BY SessionDate
            """,
            (data["recurring_group_id"],)
        ).fetchall()

        assert len(rows) == 4

        for row, expected_date in zip(rows, expected_dates):
            assert row["StartTime"] == "10:00"
            assert row["EndTime"] == "11:00"
            assert row["ClientId"] == client_id
            assert row["SessionDate"] == expected_date
            assert row["RecurringGroupId"] == data["recurring_group_id"]

    finally:
        db.close()


def test_create_session_invalid_client(client, empty_db):
    monday = get_monday()

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "11:00",
            "client_id": 99999,
            "description": "",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "recurring": "false",
            "recurring_weeks": 1
        }
    )

    assert response.status_code == 404


def test_create_session_time_conflict(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        session_date=monday.isoformat()
    )

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:30",
            "end": "11:30",
            "client_id": client_id,
            "description": "",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "recurring": "false",
            "recurring_weeks": 1
        }
    )

    assert response.status_code == 400


def test_create_session_adjacent_time_allowed(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        session_date=monday.isoformat()
    )

    response = client.post(
        "/home/session/create",
        data={
            "start": "11:00",
            "end": "12:00",
            "client_id": client_id,
            "description": "",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "recurring": "false",
            "recurring_weeks": 1
        }
    )

    assert response.status_code == 200


def test_create_session_invalid_recurring_weeks(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "11:00",
            "client_id": client_id,
            "description": "",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "recurring": "true",
            "recurring_weeks": 53
        }
    )

    assert response.status_code == 400


# ============================================================
# EDIT SINGLE SESSION
# ============================================================

def test_edit_session_ok(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    session_id = insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        description="Stary opis",
        session_date=monday.isoformat()
    )

    response = client.put(
        f"/home/session/edit/{session_id}",
        data={
            "start": "12:00",
            "end": "13:00",
            "description": "Nowy opis",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "edit_scope": "single",
            "recurring_weeks": 1
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["session_id"] == session_id
    assert data["edit_scope"] == "single"

    db = get_db()

    try:
        row = db.execute(
            """
            SELECT *
            FROM Session
            WHERE Id = ?
            """,
            (session_id,)
        ).fetchone()

        assert row["StartTime"] == "12:00"
        assert row["EndTime"] == "13:00"
        assert row["Description"] == "Nowy opis"

    finally:
        db.close()


def test_edit_session_not_exists(client, empty_db):
    monday = get_monday()

    response = client.put(
        "/home/session/edit/99999",
        data={
            "start": "10:00",
            "end": "11:00",
            "description": "",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "edit_scope": "single",
            "recurring_weeks": 1
        }
    )

    assert response.status_code == 404


def test_edit_session_conflict(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    session1_id = insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        session_date=monday.isoformat()
    )

    insert_session(
        client_id=client_id,
        start="12:00",
        end="13:00",
        session_date=monday.isoformat()
    )

    response = client.put(
        f"/home/session/edit/{session1_id}",
        data={
            "start": "12:30",
            "end": "13:30",
            "description": "",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "edit_scope": "single",
            "recurring_weeks": 1
        }
    )

    assert response.status_code == 400


def test_edit_session_adjacent_time_allowed(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    session_id = insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        session_date=monday.isoformat()
    )

    insert_session(
        client_id=client_id,
        start="12:00",
        end="13:00",
        session_date=monday.isoformat()
    )

    response = client.put(
        f"/home/session/edit/{session_id}",
        data={
            "start": "11:00",
            "end": "12:00",
            "description": "",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "edit_scope": "single",
            "recurring_weeks": 1
        }
    )

    assert response.status_code == 200


# ============================================================
# EDIT RECURRING SERIES
# ============================================================

def test_edit_recurring_series(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "11:00",
            "client_id": client_id,
            "description": "Seria",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "recurring": "true",
            "recurring_weeks": 2
        }
    )

    assert response.status_code == 200

    recurring_group_id = response.json()["recurring_group_id"]

    db = get_db()

    try:
        session_id = db.execute(
            """
            SELECT Id
            FROM Session
            WHERE RecurringGroupId = ?
            ORDER BY SessionDate
            LIMIT 1
            """,
            (recurring_group_id,)
        ).fetchone()["Id"]
    finally:
        db.close()

    response = client.put(
        f"/home/session/edit/{session_id}",
        data={
            "start": "14:00",
            "end": "15:00",
            "description": "Zmieniona seria",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "edit_scope": "series",
            "recurring_weeks": 2
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["edit_scope"] == "series"
    assert data["recurring_group_id"] == recurring_group_id
    assert data["total_count"] == 3

    db = get_db()

    try:
        rows = db.execute(
            """
            SELECT *
            FROM Session
            WHERE RecurringGroupId = ?
            ORDER BY SessionDate
            """,
            (recurring_group_id,)
        ).fetchall()

        assert len(rows) == 3

        for row in rows:
            assert row["StartTime"] == "14:00"
            assert row["EndTime"] == "15:00"
            assert row["Description"] == "Zmieniona seria"

    finally:
        db.close()


def test_edit_single_scope_on_non_recurring_session(
    client,
    empty_db
):
    client_id = insert_client()

    monday = get_monday()

    session_id = insert_session(
        client_id=client_id,
        session_date=monday.isoformat()
    )

    response = client.put(
        f"/home/session/edit/{session_id}",
        data={
            "start": "12:00",
            "end": "13:00",
            "description": "",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "edit_scope": "series",
            "recurring_weeks": 1
        }
    )

    assert response.status_code == 400


# ============================================================
# DELETE SINGLE SESSION
# ============================================================

def test_delete_session_ok(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    session_id = insert_session(
        client_id=client_id,
        session_date=monday.isoformat()
    )

    response = client.post(
        f"/home/session/delete/{session_id}",
        data={
            "delete_scope": "single"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["deleted_count"] == 1
    assert data["delete_scope"] == "single"

    db = get_db()

    try:
        row = db.execute(
            """
            SELECT *
            FROM Session
            WHERE Id = ?
            """,
            (session_id,)
        ).fetchone()

        assert row is None

    finally:
        db.close()


def test_delete_session_not_exists(client, empty_db):
    response = client.post(
        "/home/session/delete/99999",
        data={
            "delete_scope": "single"
        }
    )

    assert response.status_code == 404


# ============================================================
# DELETE RECURRING SERIES
# ============================================================

def test_delete_recurring_series_ok(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "11:00",
            "client_id": client_id,
            "description": "Seria",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "recurring": "true",
            "recurring_weeks": 3
        }
    )

    assert response.status_code == 200

    recurring_group_id = response.json()["recurring_group_id"]

    db = get_db()

    try:
        session_id = db.execute(
            """
            SELECT Id
            FROM Session
            WHERE RecurringGroupId = ?
            ORDER BY SessionDate
            LIMIT 1
            """,
            (recurring_group_id,)
        ).fetchone()["Id"]
    finally:
        db.close()

    response = client.post(
        f"/home/session/delete/{session_id}",
        data={
            "delete_scope": "series"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["delete_scope"] == "series"
    assert data["recurring_group_id"] == recurring_group_id
    assert data["deleted_count"] == 4

    db = get_db()

    try:
        rows = db.execute(
            """
            SELECT *
            FROM Session
            WHERE RecurringGroupId = ?
            """,
            (recurring_group_id,)
        ).fetchall()

        assert len(rows) == 0

    finally:
        db.close()


def test_delete_series_scope_on_non_recurring_session(
    client,
    empty_db
):
    client_id = insert_client()

    monday = get_monday()

    session_id = insert_session(
        client_id=client_id,
        session_date=monday.isoformat()
    )

    response = client.post(
        f"/home/session/delete/{session_id}",
        data={
            "delete_scope": "series"
        }
    )

    assert response.status_code == 400


# ============================================================
# INVALID DELETE / EDIT SCOPE
# ============================================================

def test_delete_session_invalid_scope(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    session_id = insert_session(
        client_id=client_id,
        session_date=monday.isoformat()
    )

    response = client.post(
        f"/home/session/delete/{session_id}",
        data={
            "delete_scope": "invalid"
        }
    )

    assert response.status_code == 400


def test_edit_session_invalid_scope(client, empty_db):
    client_id = insert_client()

    monday = get_monday()

    session_id = insert_session(
        client_id=client_id,
        session_date=monday.isoformat()
    )

    response = client.put(
        f"/home/session/edit/{session_id}",
        data={
            "start": "12:00",
            "end": "13:00",
            "description": "",
            "day_of_week": 1,
            "session_date": monday.isoformat(),
            "edit_scope": "invalid",
            "recurring_weeks": 1
        }
    )

    assert response.status_code == 400
