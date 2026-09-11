import sqlite3
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from main import app
from db import (
    get_db,
    init_db_if_not_exists,
    insert_clients,
    insert_sessions

)

TEST_DB = Path(__file__).parent / "test.db"


@pytest.fixture(scope="function")
def client():
    if TEST_DB.exists():
        TEST_DB.unlink()

    # 🔧 setup DB (TEN SAM THREAD)
    conn = sqlite3.connect(TEST_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    init_db_if_not_exists(conn)
    insert_clients(conn)
    insert_sessions(conn)

    conn.close()

    # 🔁 override dependency
    def override_get_db():
        db = sqlite3.connect(TEST_DB, check_same_thread=False)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def empty_db():
    conn = sqlite3.connect(TEST_DB, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM Client")
    cursor.execute("DELETE FROM Session")

    conn.commit()
    conn.close()
