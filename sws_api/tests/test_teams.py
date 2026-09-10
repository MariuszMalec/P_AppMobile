import sqlite3

from conftest import TEST_DB


# =========================================================
# LISTA TEAMS
# =========================================================

def test_teams_page_returns_200(client):
    response = client.get("/teams")

    assert response.status_code == 200


def test_teams_page_contains_database_data(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT Id, Name
        FROM Teams
        LIMIT 1
    """).fetchone()

    conn.close()

    assert team is not None

    response = client.get("/teams")

    assert response.status_code == 200
    assert team["Name"] in response.text


def test_teams_page_works_with_empty_db(client, empty_db):
    response = client.get("/teams")

    assert response.status_code == 200
    assert "no-data" in response.text


def test_teams_page_works_when_tables_missing(missing_tables_client):
    response = missing_tables_client.get("/teams")

    assert response.status_code == 400
    assert "Brak danych" in response.text


# =========================================================
# FILTRY
# =========================================================

def test_teams_filter_by_name(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT Name
        FROM Teams
        LIMIT 1
    """).fetchone()

    conn.close()

    assert team is not None

    name_part = team["Name"][:3]

    response = client.get(
        "/teams",
        params={"filter_name": name_part}
    )

    assert response.status_code == 200
    assert name_part in response.text


def test_teams_filter_by_trophy(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT TrophyWin
        FROM Teams
        WHERE TrophyWin IS NOT NULL
          AND TrophyWin != ''
        LIMIT 1
    """).fetchone()

    conn.close()

    if team is None:
        return

    trophy_part = team["TrophyWin"][:3]

    response = client.get(
        "/teams",
        params={"filter_trophy": trophy_part}
    )

    assert response.status_code == 200
    assert trophy_part in response.text


def test_teams_filter_by_final_result(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT FinalResult
        FROM Teams
        WHERE FinalResult IS NOT NULL
          AND FinalResult != ''
        LIMIT 1
    """).fetchone()

    conn.close()

    if team is None:
        return

    result_part = team["FinalResult"][:3]

    response = client.get(
        "/teams",
        params={"filter_result": result_part}
    )

    assert response.status_code == 200
    assert result_part in response.text


# =========================================================
# SORTOWANIE
# =========================================================

def test_teams_sort_name_asc(client):
    response = client.get(
        "/teams",
        params={"sort": "name_asc"}
    )

    assert response.status_code == 200


def test_teams_sort_name_desc(client):
    response = client.get(
        "/teams",
        params={"sort": "name_desc"}
    )

    assert response.status_code == 200


# =========================================================
# TROPHY OPTIONS
# =========================================================

def test_trophy_options_returns_200(client):
    response = client.get("/teams/trophies/options")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")


def test_trophy_options_returns_list(client):
    response = client.get("/teams/trophies/options")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert "Id" in data[0]
        assert "Name" in data[0]


# =========================================================
# TEAM PICTURE
# =========================================================

def test_team_picture_returns_picture(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT Id, Picture
        FROM Teams
        WHERE Picture IS NOT NULL
          AND Picture != ''
        LIMIT 1
    """).fetchone()

    conn.close()

    if team is None:
        return

    response = client.get(
        f"/teams/{team['Id']}/picture"
    )

    assert response.status_code == 200

    data = response.json()

    assert "picture" in data
    assert data["picture"] == team["Picture"]


def test_team_picture_for_missing_team_returns_404(client):
    response = client.get("/teams/999999999/picture")

    assert response.status_code == 404


# =========================================================
# EDIT TEAM - FORMULARZ
# =========================================================

def test_edit_team_page_returns_200(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT Id
        FROM Teams
        LIMIT 1
    """).fetchone()

    conn.close()

    assert team is not None

    response = client.get(
        f"/teams/{team['Id']}/edit"
    )

    assert response.status_code == 200


def test_edit_team_page_contains_team_data(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT Id, Name, Description, Picture
        FROM Teams
        LIMIT 1
    """).fetchone()

    conn.close()

    assert team is not None

    response = client.get(
        f"/teams/{team['Id']}/edit"
    )

    assert response.status_code == 200
    assert team["Name"] in response.text

    if team["Description"]:
        assert team["Description"] in response.text

    if team["Picture"]:
        assert team["Picture"].split("?")[0] in response.text


def test_edit_missing_team_returns_404(client):
    response = client.get("/teams/999999999/edit")

    assert response.status_code == 404


# =========================================================
# EDIT TEAM - ZAPIS
# =========================================================

def test_edit_team_updates_database(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT *
        FROM Teams
        LIMIT 1
    """).fetchone()

    conn.close()

    assert team is not None

    team_id = team["Id"]

    data = {
        "Name": "TEST TEAM EDIT",
        "Description": "TEST DESCRIPTION",
        "NationalityName": team["NationalityName"] or "",
        "Season": str(team["Season"]) if team["Season"] is not None else "",
        "TopScorer": team["TopScorer"] or "",
        "Picture": team["Picture"] or "/static/images/test.png",
        "FinalResult": team["FinalResult"] or "",
        "TrophyWin": "No",
        "TrophyModelId": "",
    }

    response = client.post(
        f"/teams/{team_id}/edit",
        data=data,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/teams"

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    updated = conn.execute("""
        SELECT *
        FROM Teams
        WHERE Id = ?
    """, (team_id,)).fetchone()

    conn.close()

    assert updated is not None
    assert updated["Name"] == "TEST TEAM EDIT"
    assert updated["Description"] == "TEST DESCRIPTION"
    assert updated["TrophyWin"] == "No"
    assert updated["TrophyModelId"] is None


def test_edit_team_empty_name_returns_400(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT Id
        FROM Teams
        LIMIT 1
    """).fetchone()

    conn.close()

    assert team is not None

    response = client.post(
        f"/teams/{team['Id']}/edit",
        data={
            "Name": "   ",
            "Description": "",
            "NationalityName": "",
            "Season": "",
            "TopScorer": "",
            "Picture": "",
            "FinalResult": "",
            "TrophyWin": "No",
            "TrophyModelId": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400


# =========================================================
# CREATE TEAM
# =========================================================

def test_create_team_redirects_to_teams(client):
    data = {
        "Name": "TEST NEW TEAM",
        "Description": "Test description",
        "NationalityName": "Poland",
        "Season": "2099",
        "TopScorer": "Test Scorer",
        "Picture": "/static/images/test.png",
        "FinalResult": "TEST NEW TEAM 2:0",
        "TrophyWin": "No",
        "TrophyModelId": "",
    }

    response = client.post(
        "/teams/create",
        data=data,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/teams"


def test_create_team_inserts_into_database(client):
    team_name = "TEST INSERT TEAM"

    data = {
        "Name": team_name,
        "Description": "Inserted description",
        "NationalityName": "Poland",
        "Season": "2098",
        "TopScorer": "Test Player",
        "Picture": "/static/images/test.png",
        "FinalResult": "TEST INSERT TEAM 3:1",
        "TrophyWin": "No",
        "TrophyModelId": "",
    }

    response = client.post(
        "/teams/create",
        data=data,
        follow_redirects=False,
    )

    assert response.status_code == 303

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT *
        FROM Teams
        WHERE Name = ?
          AND Season = ?
    """, (team_name, 2098)).fetchone()

    conn.close()

    assert team is not None
    assert team["Description"] == "Inserted description"
    assert team["FinalResult"] == "TEST INSERT TEAM 3:1"
    assert team["TrophyWin"] == "No"
    assert team["TrophyModelId"] is None


def test_create_team_empty_name_returns_200_with_error(client):
    response = client.post(
        "/teams/create",
        data={
            "Name": "   ",
            "Description": "",
            "NationalityName": "",
            "Season": "",
            "TopScorer": "",
            "Picture": "",
            "FinalResult": "",
            "TrophyWin": "No",
            "TrophyModelId": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert "Team name cannot be empty" in response.text


# =========================================================
# CREATE TEAM - DUPLIKAT
# =========================================================

def test_create_duplicate_team_returns_error(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT Name, Season, TrophyWin
        FROM Teams
        LIMIT 1
    """).fetchone()

    conn.close()

    assert team is not None

    response = client.post(
        "/teams/create",
        data={
            "Name": team["Name"],
            "Description": "Duplicate",
            "NationalityName": "",
            "Season": (
                str(team["Season"])
                if team["Season"] is not None
                else ""
            ),
            "TopScorer": "",
            "Picture": "/static/images/test.png",
            "FinalResult": "",
            "TrophyWin": team["TrophyWin"] or "No",
            "TrophyModelId": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert "already exists" in response.text


# =========================================================
# BULK CREATE
# =========================================================

def test_bulk_create_teams(client):
    data = [
        {
            "Name": "BULK TEAM 1",
            "Description": "Bulk 1",
            "NationalityName": "Poland",
            "Season": 2091,
            "TopScorer": "Player 1",
            "Picture": "/static/images/1.png",
            "FinalResult": "2:0",
            "TrophyWin": "No",
            "TrophyModelId": None,
        },
        {
            "Name": "BULK TEAM 2",
            "Description": "Bulk 2",
            "NationalityName": "Germany",
            "Season": 2092,
            "TopScorer": "Player 2",
            "Picture": "/static/images/2.png",
            "FinalResult": "1:0",
            "TrophyWin": "No",
            "TrophyModelId": None,
        },
    ]

    response = client.post(
        "/teams/bulk",
        json=data,
    )

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "ok"
    assert result["inserted"] == 2


def test_bulk_create_empty_list_returns_400(client):
    response = client.post(
        "/teams/bulk",
        json=[],
    )

    assert response.status_code == 400
    assert "Empty teams list" in response.text


def test_bulk_create_team_without_name_returns_400(client):
    response = client.post(
        "/teams/bulk",
        json=[
            {
                "Name": "",
                "Description": "Invalid",
                "Season": 2090,
            }
        ],
    )

    assert response.status_code == 400
    assert "Team name cannot be empty" in response.text


# =========================================================
# DELETE TEAM
# =========================================================

def test_delete_team_returns_redirect(client):
    # Tworzymy osobny rekord tylko na potrzeby testu.
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Teams
        (Name, Description, NationalityName, Season, TopScorer,
         Picture, FinalResult, TrophyWin, TrophyModelId)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "TEST DELETE TEAM",
        "",
        "",
        2097,
        "",
        "",
        "",
        "No",
        None,
    ))

    team_id = cursor.lastrowid

    conn.commit()
    conn.close()

    response = client.post(
        f"/teams/{team_id}/delete",
        data={},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/teams"


def test_delete_team_removes_from_database(client):
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Teams
        (Name, Description, NationalityName, Season, TopScorer,
         Picture, FinalResult, TrophyWin, TrophyModelId)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "TEST DELETE CHECK",
        "",
        "",
        2096,
        "",
        "",
        "",
        "No",
        None,
    ))

    team_id = cursor.lastrowid

    conn.commit()
    conn.close()

    response = client.post(
        f"/teams/{team_id}/delete",
        data={},
        follow_redirects=False,
    )

    assert response.status_code == 303

    conn = sqlite3.connect(TEST_DB)

    deleted = conn.execute("""
        SELECT Id
        FROM Teams
        WHERE Id = ?
    """, (team_id,)).fetchone()

    conn.close()

    assert deleted is None


def test_delete_missing_team_returns_404(client):
    response = client.post(
        "/teams/999999999/delete",
        data={},
        follow_redirects=False,
    )

    assert response.status_code == 404


# =========================================================
# TROPHIES BY SEASON
# =========================================================

def test_trophies_by_season_returns_200(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT Id
        FROM Teams
        LIMIT 1
    """).fetchone()

    conn.close()

    assert team is not None

    response = client.get(
        f"/teams/{team['Id']}/trophies_by_season"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_trophies_by_season_missing_team_returns_404(client):
    response = client.get(
        "/teams/999999999/trophies_by_season"
    )

    assert response.status_code == 404


# =========================================================
# TOPSCORER
# =========================================================

def test_topscorer_page_returns_200(client):
    response = client.get("/teams/topscorer")

    assert response.status_code == 200


def test_topscorer_filter_works(client):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    team = conn.execute("""
        SELECT TopScorer
        FROM Teams
        WHERE TopScorer IS NOT NULL
          AND TopScorer != ''
        LIMIT 1
    """).fetchone()

    conn.close()

    if team is None:
        return

    scorer_part = team["TopScorer"][:3]

    response = client.get(
        "/teams/topscorer",
        params={"topscorer": scorer_part}
    )

    assert response.status_code == 200
    assert scorer_part in response.text
