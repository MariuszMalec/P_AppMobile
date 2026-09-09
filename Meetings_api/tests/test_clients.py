import sqlite3

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


# ============================================================
# CLIENTS PAGE
# ============================================================

def test_clients_page_returns_200(client):
    response = client.get("/clients/")

    assert response.status_code == 200


# ============================================================
# GET CLIENTS LIST
# ============================================================

def test_get_clients_list_empty(client, empty_db):
    response = client.get("/clients/list")

    assert response.status_code == 200
    assert response.json() == []


def test_get_clients_list_returns_client(client, empty_db):
    insert_client(
        first_name="Jan",
        last_name="Kowalski"
    )

    response = client.get("/clients/list")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["FirstName"] == "Jan"
    assert data[0]["LastName"] == "Kowalski"


# ============================================================
# GET SINGLE CLIENT
# ============================================================

def test_get_client(client, empty_db):
    client_id = insert_client(
        first_name="Jan",
        last_name="Kowalski",
        age=30,
        description="Opis",
        phone="123456789",
        gender="male"
    )

    response = client.get(f"/clients/{client_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["Id"] == client_id
    assert data["FirstName"] == "Jan"
    assert data["LastName"] == "Kowalski"
    assert data["Age"] == 30
    assert data["Description"] == "Opis"
    assert data["Phone"] == "123456789"
    assert data["Gender"] == "male"


def test_get_client_not_exists(client, empty_db):
    response = client.get("/clients/99999")

    assert response.status_code == 404


# ============================================================
# CREATE CLIENT
# ============================================================

def test_create_client_ok(client, empty_db):
    response = client.post(
        "/clients/create",
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

    assert "client_id" in data

    client_id = data["client_id"]

    db = get_db()

    try:
        row = db.execute(
            """
            SELECT *
            FROM Client
            WHERE Id = ?
            """,
            (client_id,)
        ).fetchone()

        assert row is not None
        assert row["FirstName"] == "Piotr"
        assert row["LastName"] == "Testowy"
        assert row["Age"] == 25
        assert row["Description"] == "Opis"
        assert row["Phone"] == "555666777"
        assert row["Gender"] == "male"

    finally:
        db.close()


def test_create_client_without_first_name(client, empty_db):
    response = client.post(
        "/clients/create",
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


def test_create_client_without_last_name(client, empty_db):
    response = client.post(
        "/clients/create",
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


def test_create_client_negative_age(client, empty_db):
    response = client.post(
        "/clients/create",
        data={
            "first_name": "Piotr",
            "last_name": "Testowy",
            "age": -1,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 400


def test_create_client_invalid_gender(client, empty_db):
    response = client.post(
        "/clients/create",
        data={
            "first_name": "Piotr",
            "last_name": "Testowy",
            "age": 25,
            "description": "",
            "phone": "",
            "gender": "invalid"
        }
    )

    assert response.status_code == 400


# ============================================================
# CREATE CLIENT - DUPLICATE
# ============================================================

def test_create_client_duplicate(client, empty_db):
    insert_client(
        first_name="Jan",
        last_name="Kowalski"
    )

    response = client.post(
        "/clients/create",
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
    assert "Klient o takim imieniu i nazwisku już istnieje" in response.text


def test_create_client_duplicate_case_insensitive(client, empty_db):
    insert_client(
        first_name="Jan",
        last_name="Kowalski"
    )

    response = client.post(
        "/clients/create",
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
    assert "Klient o takim imieniu i nazwisku już istnieje" in response.text


# ============================================================
# EDIT CLIENT
# ============================================================

def test_edit_client_ok(client, empty_db):
    client_id = insert_client(
        first_name="Jan",
        last_name="Kowalski",
        age=30,
        description="Stary opis",
        phone="123456789",
        gender="male"
    )

    response = client.put(
        f"/clients/edit/{client_id}",
        data={
            "first_name": "Jan",
            "last_name": "Kowalski",
            "age": 40,
            "description": "Nowy opis",
            "phone": "987654321",
            "gender": "female"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["client_id"] == client_id

    db = get_db()

    try:
        row = db.execute(
            """
            SELECT *
            FROM Client
            WHERE Id = ?
            """,
            (client_id,)
        ).fetchone()

        assert row is not None
        assert row["FirstName"] == "Jan"
        assert row["LastName"] == "Kowalski"
        assert row["Age"] == 40
        assert row["Description"] == "Nowy opis"
        assert row["Phone"] == "987654321"
        assert row["Gender"] == "female"

    finally:
        db.close()


def test_edit_client_not_exists(client, empty_db):
    response = client.put(
        "/clients/edit/99999",
        data={
            "first_name": "Jan",
            "last_name": "Kowalski",
            "age": 30,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 404


def test_edit_client_duplicate(client, empty_db):
    client1_id = insert_client(
        first_name="Jan",
        last_name="Kowalski"
    )

    insert_client(
        first_name="Piotr",
        last_name="Testowy"
    )

    response = client.put(
        f"/clients/edit/{client1_id}",
        data={
            "first_name": "Piotr",
            "last_name": "Testowy",
            "age": 30,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 400
    assert "Klient o takim imieniu i nazwisku już istnieje" in response.text


def test_edit_client_duplicate_case_insensitive(client, empty_db):
    client1_id = insert_client(
        first_name="Jan",
        last_name="Kowalski"
    )

    insert_client(
        first_name="Piotr",
        last_name="Testowy"
    )

    response = client.put(
        f"/clients/edit/{client1_id}",
        data={
            "first_name": "PIOTR",
            "last_name": "TESTOWY",
            "age": 30,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 400
    assert "Klient o takim imieniu i nazwisku już istnieje" in response.text


# ============================================================
# EDIT CLIENT - VALIDATION
# ============================================================

def test_edit_client_without_first_name(client, empty_db):
    client_id = insert_client()

    response = client.put(
        f"/clients/edit/{client_id}",
        data={
            "first_name": "",
            "last_name": "Kowalski",
            "age": 30,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 422


def test_edit_client_without_last_name(client, empty_db):
    client_id = insert_client()

    response = client.put(
        f"/clients/edit/{client_id}",
        data={
            "first_name": "Jan",
            "last_name": "",
            "age": 30,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 422


def test_edit_client_negative_age(client, empty_db):
    client_id = insert_client()

    response = client.put(
        f"/clients/edit/{client_id}",
        data={
            "first_name": "Jan",
            "last_name": "Kowalski",
            "age": -1,
            "description": "",
            "phone": "",
            "gender": "male"
        }
    )

    assert response.status_code == 400


def test_edit_client_invalid_gender(client, empty_db):
    client_id = insert_client()

    response = client.put(
        f"/clients/edit/{client_id}",
        data={
            "first_name": "Jan",
            "last_name": "Kowalski",
            "age": 30,
            "description": "",
            "phone": "",
            "gender": "invalid"
        }
    )

    assert response.status_code == 400


# ============================================================
# DELETE CLIENT
# ============================================================

def test_delete_client_ok(client, empty_db):
    client_id = insert_client(
        first_name="Jan",
        last_name="Kowalski"
    )

    response = client.delete(
        f"/clients/delete/{client_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["client_id"] == client_id
    assert "deleted_sessions" in data
    assert isinstance(data["deleted_sessions"], int)

    db = get_db()

    try:
        row = db.execute(
            """
            SELECT *
            FROM Client
            WHERE Id = ?
            """,
            (client_id,)
        ).fetchone()

        assert row is not None
        assert row["IsActive"] == 0

    finally:
        db.close()


def test_deleted_client_not_in_active_list(client, empty_db):
    client_id = insert_client(
        first_name="Jan",
        last_name="Kowalski"
    )

    response = client.delete(
        f"/clients/delete/{client_id}"
    )

    assert response.status_code == 200

    response = client.get("/clients/list")

    assert response.status_code == 200

    data = response.json()

    ids = [item["Id"] for item in data]

    assert client_id not in ids


def test_delete_client_not_exists(client, empty_db):
    response = client.delete(
        "/clients/delete/99999"
    )

    assert response.status_code == 404