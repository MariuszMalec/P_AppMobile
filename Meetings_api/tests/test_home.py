import sqlite3
from datetime import datetime, timedelta

from db import DB_PATH
from conftest import TEST_DB


# ============================================================
# Pomocnicze funkcje
# ============================================================

def get_db():
    db = sqlite3.connect(TEST_DB, check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db


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
    session_date=None
):
    if session_date is None:
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        session_date = monday.isoformat()

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
                SessionDate
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                start,
                end,
                client_id,
                description,
                day_of_week,
                session_date
            )
        )

        session_id = cursor.lastrowid

        db.commit()

        return session_id

    finally:
        db.close()


# ============================================================
# HOME PAGE
# ============================================================

def test_home_page_returns_200(client):
    response = client.get("/home/")

    assert response.status_code == 200


def test_home_page_contains_days(client):
    response = client.get("/home/")

    assert response.status_code == 200

    assert "Poniedziałek" in response.text
    assert "Wtorek" in response.text
    assert "Środa" in response.text
    assert "Czwartek" in response.text
    assert "Piątek" in response.text


def test_home_page_contains_session(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        description="Sesja testowa",
        day_of_week=1,
        session_date=monday.isoformat()
    )

    response = client.get("/home/?week_offset=0")

    assert response.status_code == 200
    assert "Sesja testowa" in response.text


# ============================================================
# GET CLIENTS
# ============================================================

def test_get_clients_empty(client, empty_db):
    response = client.get("/home/get_clients")

    assert response.status_code == 200
    assert response.json() == []


def test_get_clients_returns_client(client, empty_db):
    insert_client(
        first_name="Jan",
        last_name="Kowalski"
    )

    response = client.get("/home/get_clients")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["FirstName"] == "Jan"
    assert data[0]["LastName"] == "Kowalski"


# ============================================================
# CREATE CLIENT
# ============================================================

def test_create_client_ok(client, empty_db):
    response = client.post(
        "/home/client/create",
        data={
            "first_name": "Piotr",
            "last_name": "Testowy",
            "age": 25,
            "description": "Opis",
            "phone": "555666777",
            "gender": "male"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["message"] == "Klient utworzony"

    db = get_db()

    try:
        row = db.execute(
            """
            SELECT *
            FROM Client
            WHERE FirstName = ?
              AND LastName = ?
            """,
            ("Piotr", "Testowy")
        ).fetchone()

        assert row is not None
        assert row["Age"] == 25
        assert row["Description"] == "Opis"
        assert row["Phone"] == "555666777"
        assert row["Gender"] == "male"

    finally:
        db.close()


def test_create_client_fails_without_first_name(client, empty_db):
    response = client.post(
        "/home/client/create",
        data={
            "first_name": "",
            "last_name": "Testowy",
            "age": 25,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 422


def test_create_client_fails_without_last_name(client, empty_db):
    response = client.post(
        "/home/client/create",
        data={
            "first_name": "Piotr",
            "last_name": "",
            "age": 25,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 422


def test_create_client_duplicate(client, empty_db):
    insert_client(
        first_name="Jan",
        last_name="Kowalski"
    )

    response = client.post(
        "/home/client/create",
        data={
            "first_name": "Jan",
            "last_name": "Kowalski",
            "age": 30,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 400
    assert "Klient już istnieje" in response.text


def test_create_client_duplicate_case_insensitive(client, empty_db):
    insert_client(
        first_name="Jan",
        last_name="Kowalski"
    )

    response = client.post(
        "/home/client/create",
        data={
            "first_name": "JAN",
            "last_name": "KOWALSKI",
            "age": 30,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 400
    assert "Klient już istnieje" in response.text


# ============================================================
# CREATE SESSION
# ============================================================

def test_create_session_ok(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "11:00",
            "client_id": client_id,
            "description": "Nowa sesja",
            "day_of_week": 1,
            "session_date": monday.isoformat()
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["message"] == "Sesja utworzona"

    db = get_db()

    try:
        row = db.execute(
            """
            SELECT *
            FROM Session
            WHERE Description = ?
            """,
            ("Nowa sesja",)
        ).fetchone()

        assert row is not None
        assert row["StartTime"] == "10:00"
        assert row["EndTime"] == "11:00"
        assert row["ClientId"] == client_id
        assert row["DayOfWeek"] == 1
        assert row["SessionDate"] == monday.isoformat()

    finally:
        db.close()


def test_create_session_invalid_time(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    response = client.post(
        "/home/session/create",
        data={
            "start": "11:00",
            "end": "10:00",
            "client_id": client_id,
            "description": "Test",
            "day_of_week": 1,
            "session_date": monday.isoformat()
        }
    )

    assert response.status_code == 400
    assert "Godzina zakończenia musi być późniejsza niż rozpoczęcia" in response.text


def test_create_session_same_start_end(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "10:00",
            "client_id": client_id,
            "description": "Test",
            "day_of_week": 1,
            "session_date": monday.isoformat()
        }
    )

    assert response.status_code == 400


def test_create_session_invalid_day(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "11:00",
            "client_id": client_id,
            "description": "Test",
            "day_of_week": 8,
            "session_date": monday.isoformat()
        }
    )

    assert response.status_code == 400


def test_create_session_invalid_date(client, empty_db):
    client_id = insert_client()

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "11:00",
            "client_id": client_id,
            "description": "Test",
            "day_of_week": 1,
            "session_date": "2026-99-99"
        }
    )

    assert response.status_code == 400


def test_create_session_client_not_exists(client, empty_db):
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:00",
            "end": "11:00",
            "client_id": 99999,
            "description": "Test",
            "day_of_week": 1,
            "session_date": monday.isoformat()
        }
    )

    assert response.status_code == 404
    assert "Nie ma takiego klienta" in response.text


def test_create_session_conflict(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    session_date = monday.isoformat()

    insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        description="Istniejąca",
        day_of_week=1,
        session_date=session_date
    )

    response = client.post(
        "/home/session/create",
        data={
            "start": "10:30",
            "end": "11:30",
            "client_id": client_id,
            "description": "Konflikt",
            "day_of_week": 1,
            "session_date": session_date
        }
    )

    assert response.status_code == 400
    assert "Konflikt" in response.text


def test_create_session_adjacent_time_ok(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    session_date = monday.isoformat()

    insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        description="Pierwsza",
        day_of_week=1,
        session_date=session_date
    )

    response = client.post(
        "/home/session/create",
        data={
            "start": "11:00",
            "end": "12:00",
            "client_id": client_id,
            "description": "Druga",
            "day_of_week": 1,
            "session_date": session_date
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


# ============================================================
# EDIT SESSION
# ============================================================

def test_edit_session_ok(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    session_date = monday.isoformat()

    session_id = insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        description="Stara sesja",
        day_of_week=1,
        session_date=session_date
    )

    response = client.put(
        f"/home/session/edit/{session_id}",
        data={
            "start": "12:00",
            "end": "13:00",
            "description": "Zmieniona sesja",
            "day_of_week": 1
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["message"] == "Sesja zaktualizowana"

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

        assert row is not None
        assert row["StartTime"] == "12:00"
        assert row["EndTime"] == "13:00"
        assert row["Description"] == "Zmieniona sesja"

    finally:
        db.close()


def test_edit_session_not_exists(client, empty_db):
    response = client.put(
        "/home/session/edit/99999",
        data={
            "start": "12:00",
            "end": "13:00",
            "description": "Test",
            "day_of_week": 1
        }
    )

    assert response.status_code == 404
    assert "Sesja nie istnieje" in response.text


def test_edit_session_invalid_time(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    session_id = insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        day_of_week=1,
        session_date=monday.isoformat()
    )

    response = client.put(
        f"/home/session/edit/{session_id}",
        data={
            "start": "14:00",
            "end": "13:00",
            "description": "Test",
            "day_of_week": 1
        }
    )

    assert response.status_code == 400
    assert "Godzina zakończenia musi być późniejsza niż rozpoczęcia" in response.text


def test_edit_session_conflict(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    session_date = monday.isoformat()

    session1 = insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        description="Pierwsza",
        day_of_week=1,
        session_date=session_date
    )

    session2 = insert_session(
        client_id=client_id,
        start="12:00",
        end="13:00",
        description="Druga",
        day_of_week=1,
        session_date=session_date
    )

    response = client.put(
        f"/home/session/edit/{session2}",
        data={
            "start": "10:30",
            "end": "11:30",
            "description": "Druga zmieniona",
            "day_of_week": 1
        }
    )

    assert response.status_code == 400
    assert "Konflikt" in response.text


def test_edit_session_same_session_not_conflict(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    session_date = monday.isoformat()

    session_id = insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        description="Sesja",
        day_of_week=1,
        session_date=session_date
    )

    response = client.put(
        f"/home/session/edit/{session_id}",
        data={
            "start": "10:30",
            "end": "11:30",
            "description": "Sesja zmieniona",
            "day_of_week": 1
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


# ============================================================
# DELETE SESSION
# ============================================================

def test_delete_session_ok(client, empty_db):
    client_id = insert_client()

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    session_id = insert_session(
        client_id=client_id,
        start="10:00",
        end="11:00",
        description="Do usunięcia",
        day_of_week=1,
        session_date=monday.isoformat()
    )

    response = client.post(
        f"/home/session/delete/{session_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["message"] == "Sesja usunięta"

    db = get_db()

    try:
        row = db.execute(
            """
            SELECT Id
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
        "/home/session/delete/99999"
    )

    assert response.status_code == 404
    assert "Sesja nie istnieje" in response.text