import sqlite3
import pytest
from fastapi.testclient import TestClient

from main import app

from conftest import TEST_DB


# ============================================================
# HELPERS
# ============================================================

def get_test_db():
    """
    Otwiera bezpośrednie połączenie z testową bazą SQLite.
    Nie używamy tutaj db.get_db(), ponieważ jest to generator
    zależności FastAPI z yield.
    """
    conn = sqlite3.connect(TEST_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def clear_orders():
    """
    Usuwa wszystkie Orders z testowej bazy.
    """
    conn = get_test_db()

    try:
        conn.execute("DELETE FROM Orders")
        conn.commit()
    finally:
        conn.close()


def get_order(order_id):
    """
    Pobiera zamówienie po ID.
    """
    conn = get_test_db()

    try:
        return conn.execute(
            "SELECT * FROM Orders WHERE Id = ?",
            (order_id,)
        ).fetchone()
    finally:
        conn.close()


def get_order_by_zlecenie(zlecenie):
    """
    Pobiera zamówienie po numerze zlecenia.
    """
    conn = get_test_db()

    try:
        return conn.execute(
            "SELECT * FROM Orders WHERE Zlecenie = ?",
            (zlecenie,)
        ).fetchone()
    finally:
        conn.close()


def insert_test_order(
    machine_id=1,
    start_date="2026-09-10T10:00",
    hours=8,
    zlecenie="TEST-001",
    project_name="Projekt testowy",
    exw="2026-09-20",
    color="#ff0000",
):
    """
    Dodaje testowe zamówienie bezpośrednio do bazy.
    Zwraca ID nowego zamówienia.
    """
    conn = get_test_db()

    try:
        cursor = conn.execute(
            """
            INSERT INTO Orders (
                Name,
                Zlecenie,
                Haslo,
                ProjectName,
                TypeOfBlade,
                Exw,
                StartDate,
                Hours,
                ExistNC,
                ExistCMM,
                ExistMaterial,
                MachineId,
                Color
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "IMR",
                zlecenie,
                "0",
                project_name,
                "k1",
                exw,
                start_date,
                hours,
                0,
                0,
                0,
                machine_id,
                color,
            )
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


# ============================================================
# GET /harmonogram
# ============================================================

def test_harmonogram_page_returns_200(client: TestClient):
    response = client.get("/harmonogram")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_harmonogram_page_contains_machines(client: TestClient):
    response = client.get("/harmonogram")

    assert response.status_code == 200

    # Maszyny są seedowane przez conftest.py
    assert "LINIA1" in response.text
    assert "LINIA2" in response.text
    assert "LINIA3" in response.text


# ============================================================
# POST /harmonogram/add
# ============================================================

def test_add_order_ok(client: TestClient):
    clear_orders()

    payload = {
        "MachineId": 1,
        "StartDate": "2026-09-10T08:00",
        "ProjectName": "Nowy projekt",
        "Zlecenie": "ADD-001",
        "Hours": 12,
        "Exw": "2026-09-20",
        "ExistNC": 1,
        "ExistCMM": 0,
        "ExistMaterial": 1,
        "Color": "#123456",
    }

    response = client.post("/harmonogram/add", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order_by_zlecenie("ADD-001")

    assert order is not None
    assert order["MachineId"] == 1
    assert order["StartDate"] == "2026-09-10T08:00"
    assert order["ProjectName"] == "Nowy projekt"
    assert order["Hours"] == 12
    assert order["ExistNC"] == 1
    assert order["ExistCMM"] == 0
    assert order["ExistMaterial"] == 1
    assert order["Color"] == "#123456"


def test_add_order_default_values(client: TestClient):
    clear_orders()

    payload = {
        "MachineId": 2,
        "StartDate": "2026-09-11T10:00",
        "Zlecenie": "ADD-DEFAULT",
        "Hours": 8,
        "Exw": "2026-09-21",
    }

    response = client.post("/harmonogram/add", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order_by_zlecenie("ADD-DEFAULT")

    assert order is not None
    assert order["MachineId"] == 2
    assert order["Hours"] == 8
    assert order["ProjectName"] == ""
    assert order["ExistNC"] == 0
    assert order["ExistCMM"] == 0
    assert order["ExistMaterial"] == 0
    assert order["Color"] == "#f4f4f4"


def test_add_order_custom_color(client: TestClient):
    clear_orders()

    payload = {
        "MachineId": 3,
        "StartDate": "2026-09-12T12:00",
        "Zlecenie": "ADD-COLOR",
        "Hours": 6,
        "Exw": "2026-09-22",
        "Color": "#abcdef",
    }

    response = client.post("/harmonogram/add", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order_by_zlecenie("ADD-COLOR")

    assert order is not None
    assert order["Color"] == "#abcdef"


# ============================================================
# POST /harmonogram/edit/{order_id}
# ============================================================

def test_edit_order_ok(client: TestClient):
    clear_orders()

    order_id = insert_test_order(
        machine_id=1,
        start_date="2026-09-10T08:00",
        hours=8,
        zlecenie="EDIT-001",
        project_name="Stary projekt",
        exw="2026-09-20",
        color="#111111",
    )

    payload = {
        "MachineId": 2,
        "StartDate": "2026-09-11T10:00",
        "Exw": "2026-09-25",
        "Hours": 16,
        "ExistNC": 1,
        "ExistCMM": 1,
        "ExistMaterial": 0,
        "Zlecenie": "EDIT-002",
        "ProjectName": "Nowy projekt",
        "Color": "#222222",
    }

    response = client.post(
        f"/harmonogram/edit/{order_id}",
        json=payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order(order_id)

    assert order is not None
    assert order["MachineId"] == 2
    assert order["StartDate"] == "2026-09-11T10:00"
    assert order["Exw"] == "2026-09-25"
    assert order["Hours"] == 16
    assert order["ExistNC"] == 1
    assert order["ExistCMM"] == 1
    assert order["ExistMaterial"] == 0
    assert order["Zlecenie"] == "EDIT-002"
    assert order["ProjectName"] == "Nowy projekt"
    assert order["Color"] == "#222222"


def test_edit_order_color(client: TestClient):
    clear_orders()

    order_id = insert_test_order(
        machine_id=1,
        start_date="2026-09-10T08:00",
        hours=8,
        zlecenie="EDIT-COLOR",
        exw="2026-09-20",
        color="#111111",
    )

    payload = {
        "MachineId": 1,
        "StartDate": "2026-09-10T08:00",
        "Exw": "2026-09-20",
        "Hours": 8,
        "ExistNC": 0,
        "ExistCMM": 0,
        "ExistMaterial": 0,
        "Zlecenie": "EDIT-COLOR",
        "ProjectName": "Projekt",
        "Color": "#00ff00",
    }

    response = client.post(
        f"/harmonogram/edit/{order_id}",
        json=payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order(order_id)

    assert order["Color"] == "#00ff00"


def test_edit_order_conflict(client: TestClient):
    clear_orders()

    first_id = insert_test_order(
        machine_id=1,
        start_date="2026-09-10T10:00",
        hours=4,
        zlecenie="CONFLICT-001",
        exw="2026-09-20",
    )

    second_id = insert_test_order(
        machine_id=1,
        start_date="2026-09-10T16:00",
        hours=4,
        zlecenie="CONFLICT-002",
        exw="2026-09-20",
    )

    payload = {
        "MachineId": 1,
        "StartDate": "2026-09-10T12:00",
        "Exw": "2026-09-20",
        "Hours": 4,
        "ExistNC": 0,
        "ExistCMM": 0,
        "ExistMaterial": 0,
        "Zlecenie": "CONFLICT-002",
        "ProjectName": "Projekt",
        "Color": "#ff0000",
    }

    response = client.post(
        f"/harmonogram/edit/{second_id}",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "error"
    assert str(first_id) in data["message"]

    # Drugie zamówienie nie powinno zostać zmienione
    order = get_order(second_id)

    assert order["StartDate"] == "2026-09-10T16:00"
    assert order["MachineId"] == 1


def test_edit_order_adjacent_time_is_allowed(client: TestClient):
    clear_orders()

    insert_test_order(
        machine_id=1,
        start_date="2026-09-10T10:00",
        hours=4,
        zlecenie="ADJ-001",
        exw="2026-09-20",
    )

    second_id = insert_test_order(
        machine_id=1,
        start_date="2026-09-10T18:00",
        hours=4,
        zlecenie="ADJ-002",
        exw="2026-09-20",
    )

    # Pierwszy order kończy się o 14:00.
    # Drugi zaczyna się dokładnie o 14:00.
    # Nie powinno być konfliktu.
    payload = {
        "MachineId": 1,
        "StartDate": "2026-09-10T14:00",
        "Exw": "2026-09-20",
        "Hours": 4,
        "ExistNC": 0,
        "ExistCMM": 0,
        "ExistMaterial": 0,
        "Zlecenie": "ADJ-002",
        "ProjectName": "Projekt",
        "Color": "#ff0000",
    }

    response = client.post(
        f"/harmonogram/edit/{second_id}",
        json=payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order(second_id)

    assert order["StartDate"] == "2026-09-10T14:00"


def test_edit_order_move_to_another_machine(client: TestClient):
    clear_orders()

    insert_test_order(
        machine_id=1,
        start_date="2026-09-10T10:00",
        hours=8,
        zlecenie="MACHINE-001",
        exw="2026-09-20",
    )

    second_id = insert_test_order(
        machine_id=2,
        start_date="2026-09-10T10:00",
        hours=8,
        zlecenie="MACHINE-002",
        exw="2026-09-20",
    )

    payload = {
        "MachineId": 1,
        "StartDate": "2026-09-10T18:00",
        "Exw": "2026-09-20",
        "Hours": 8,
        "ExistNC": 0,
        "ExistCMM": 0,
        "ExistMaterial": 0,
        "Zlecenie": "MACHINE-002",
        "ProjectName": "Projekt",
        "Color": "#123456",
    }

    response = client.post(
        f"/harmonogram/edit/{second_id}",
        json=payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order(second_id)

    assert order["MachineId"] == 1
    assert order["StartDate"] == "2026-09-10T18:00"


# ============================================================
# POST /harmonogram/move/{order_id}
# ============================================================

def test_move_order_ok(client: TestClient):
    clear_orders()

    order_id = insert_test_order(
        machine_id=1,
        start_date="2026-09-10T08:00",
        hours=4,
        zlecenie="MOVE-001",
        exw="2026-09-20",
    )

    payload = {
        "MachineId": 2,
        "StartDate": "2026-09-11T10:00",
        "Hours": 4,
    }

    response = client.post(
        f"/harmonogram/move/{order_id}",
        json=payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order(order_id)

    assert order["MachineId"] == 2
    assert order["StartDate"] == "2026-09-11T10:00"


def test_move_order_not_enough_hours(client: TestClient):
    clear_orders()

    insert_test_order(
        machine_id=2,
        start_date="2026-09-11T10:00",
        hours=20,
        zlecenie="MOVE-FULL-001",
        exw="2026-09-20",
    )

    order_id = insert_test_order(
        machine_id=1,
        start_date="2026-09-10T08:00",
        hours=5,
        zlecenie="MOVE-FULL-002",
        exw="2026-09-20",
    )

    payload = {
        "MachineId": 2,
        "StartDate": "2026-09-11T10:00",
        "Hours": 5,
    }

    response = client.post(
        f"/harmonogram/move/{order_id}",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "error"
    assert data["message"] == "Nie ma wystarczającej liczby godzin w tym dniu!"

    # Order nie powinien zostać przesunięty
    order = get_order(order_id)

    assert order["MachineId"] == 1
    assert order["StartDate"] == "2026-09-10T08:00"


def test_move_order_exactly_24_hours_is_allowed(client: TestClient):
    clear_orders()

    insert_test_order(
        machine_id=2,
        start_date="2026-09-11T10:00",
        hours=20,
        zlecenie="MOVE-24-001",
        exw="2026-09-20",
    )

    order_id = insert_test_order(
        machine_id=1,
        start_date="2026-09-10T08:00",
        hours=4,
        zlecenie="MOVE-24-002",
        exw="2026-09-20",
    )

    payload = {
        "MachineId": 2,
        "StartDate": "2026-09-11T10:00",
        "Hours": 4,
    }

    response = client.post(
        f"/harmonogram/move/{order_id}",
        json=payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order(order_id)

    assert order["MachineId"] == 2
    assert order["StartDate"] == "2026-09-11T10:00"


# ============================================================
# POST /harmonogram/delete/{order_id}
# ============================================================

def test_delete_order_ok(client: TestClient):
    clear_orders()

    order_id = insert_test_order(
        machine_id=1,
        start_date="2026-09-10T08:00",
        hours=8,
        zlecenie="DELETE-001",
        exw="2026-09-20",
    )

    assert get_order(order_id) is not None

    response = client.post(
        f"/harmonogram/delete/{order_id}"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    assert get_order(order_id) is None


def test_delete_order_that_does_not_exist(client: TestClient):
    clear_orders()

    response = client.post(
        "/harmonogram/delete/999999"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "error"
    assert "nie istnieje" in data["message"]


# ============================================================
# FULL LIFECYCLE
# ============================================================

def test_order_full_lifecycle(client: TestClient):
    clear_orders()

    # --------------------------------------------------------
    # 1. CREATE
    # --------------------------------------------------------

    create_payload = {
        "MachineId": 1,
        "StartDate": "2026-09-10T08:00",
        "ProjectName": "Lifecycle project",
        "Zlecenie": "LIFE-001",
        "Hours": 8,
        "Exw": "2026-09-20",
        "ExistNC": 0,
        "ExistCMM": 0,
        "ExistMaterial": 0,
        "Color": "#123456",
    }

    response = client.post(
        "/harmonogram/add",
        json=create_payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order_by_zlecenie("LIFE-001")

    assert order is not None

    order_id = order["Id"]

    assert order["MachineId"] == 1
    assert order["Hours"] == 8
    assert order["Color"] == "#123456"

    # --------------------------------------------------------
    # 2. EDIT
    # --------------------------------------------------------

    edit_payload = {
        "MachineId": 2,
        "StartDate": "2026-09-11T10:00",
        "Exw": "2026-09-25",
        "Hours": 12,
        "ExistNC": 1,
        "ExistCMM": 1,
        "ExistMaterial": 0,
        "Zlecenie": "LIFE-002",
        "ProjectName": "Lifecycle changed",
        "Color": "#654321",
    }

    response = client.post(
        f"/harmonogram/edit/{order_id}",
        json=edit_payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order(order_id)

    assert order["MachineId"] == 2
    assert order["StartDate"] == "2026-09-11T10:00"
    assert order["Hours"] == 12
    assert order["Zlecenie"] == "LIFE-002"
    assert order["ProjectName"] == "Lifecycle changed"
    assert order["Color"] == "#654321"

    # --------------------------------------------------------
    # 3. MOVE
    # --------------------------------------------------------

    move_payload = {
        "MachineId": 3,
        "StartDate": "2026-09-12T12:00",
        "Hours": 12,
    }

    response = client.post(
        f"/harmonogram/move/{order_id}",
        json=move_payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    order = get_order(order_id)

    assert order["MachineId"] == 3
    assert order["StartDate"] == "2026-09-12T12:00"

    # --------------------------------------------------------
    # 4. DELETE
    # --------------------------------------------------------

    response = client.post(
        f"/harmonogram/delete/{order_id}"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    assert get_order(order_id) is None
