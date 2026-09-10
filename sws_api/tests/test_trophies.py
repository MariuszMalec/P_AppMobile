import sqlite3
from conftest import TEST_DB


# =========================================================
# LISTA TROFEÓW
# =========================================================

def test_home_page_return_status_code_200(client):
    response = client.get("/trophies")

    assert response.status_code == 200


def test_home_works_with_empty_db(client, empty_db):
    response = client.get("/trophies")

    assert response.status_code == 200
    assert "no-data" in response.text


def test_home_works_when_tables_missing(client):
    # symulujemy brak bazy / tabel
    if TEST_DB.exists():
        TEST_DB.unlink()

    response = client.get("/trophies")

    assert response.status_code == 400
    assert "Brak danych" in response.text


def test_trophies_list_contains_database_data(client):
    response = client.get("/trophies")

    assert response.status_code == 200

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    trophy = conn.execute("""
        SELECT Id, Name
        FROM Trophies
        LIMIT 1
    """).fetchone()

    conn.close()

    assert trophy is not None
    assert trophy["Name"] in response.text


# =========================================================
# EDIT - FORMULARZ
# =========================================================

def test_edit_trophy_page_returns_200(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    trophy = conn.execute("""
        SELECT Id
        FROM Trophies
        LIMIT 1
    """).fetchone()

    conn.close()

    assert trophy is not None

    response = client.get(f"/trophies/edit/{trophy['Id']}")

    assert response.status_code == 200


def test_edit_trophy_page_contains_trophy_data(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    trophy = conn.execute("""
        SELECT Id, Name, Description, Picture
        FROM Trophies
        LIMIT 1
    """).fetchone()

    conn.close()

    assert trophy is not None

    response = client.get(f"/trophies/edit/{trophy['Id']}")

    assert response.status_code == 200

    assert trophy["Name"] in response.text

    if trophy["Description"]:
        assert trophy["Description"] in response.text

    if trophy["Picture"]:
        # Jinja HTML-escape'uje "&" jako "&amp;"
        # więc sprawdzamy charakterystyczny fragment URL.
        assert trophy["Picture"].split("?")[0] in response.text

# =========================================================
# EDIT - ZAPIS
# =========================================================

def test_edit_trophy_updates_database(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    trophy = conn.execute("""
        SELECT Id, TeamModelId
        FROM Trophies
        LIMIT 1
    """).fetchone()

    conn.close()

    assert trophy is not None

    trophy_id = trophy["Id"]

    response = client.post(
        f"/trophies/edit/{trophy_id}",
        data={
            "Name": "TEST TROPHY",
            "Description": "TEST DESCRIPTION",
            "Picture": "/static/images/test.png",
            "TeamModelId": (
                str(trophy["TeamModelId"])
                if trophy["TeamModelId"] is not None
                else ""
            ),
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/trophies"

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    updated = conn.execute("""
        SELECT Name, Description, Picture, TeamModelId
        FROM Trophies
        WHERE Id = ?
    """, (trophy_id,)).fetchone()

    conn.close()

    assert updated is not None
    assert updated["Name"] == "TEST TROPHY"
    assert updated["Description"] == "TEST DESCRIPTION"
    assert updated["Picture"] == "/static/images/test.png"

    if trophy["TeamModelId"] is not None:
        assert updated["TeamModelId"] == trophy["TeamModelId"]


def test_edit_trophy_redirects_to_trophies(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    trophy = conn.execute("""
        SELECT Id, TeamModelId
        FROM Trophies
        LIMIT 1
    """).fetchone()

    conn.close()

    assert trophy is not None

    data = {
        "Name": "Redirect Test",
        "Description": "Redirect Description",
        "Picture": "/static/images/test.png",
    }

    if trophy["TeamModelId"] is not None:
        data["TeamModelId"] = str(trophy["TeamModelId"])

    response = client.post(
        f"/trophies/edit/{trophy['Id']}",
        data=data,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/trophies"
    

# =========================================================
# PUSTA BAZA - PONOWNIE
# =========================================================

def test_trophies_page_after_deleting_all_trophies(client, empty_db):
    response = client.get("/trophies")

    assert response.status_code == 200
    assert "no-data" in response.text
    assert "Brak trofeów" in response.text