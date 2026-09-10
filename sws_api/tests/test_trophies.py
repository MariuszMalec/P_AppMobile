import sys
from pathlib import Path
from freezegun import freeze_time


import sqlite3
from pathlib import Path

from conftest import TEST_DB



def test_home_page_return_status_code_200(client):
    response = client.get("/trophies")
    assert response.status_code == 200

def test_home_works_with_empty_db(client, empty_db):
    response = client.get("/trophies")

    assert response.status_code == 200
    assert "no-data" in response.text  # np. klasa w HTML


def test_home_works_when_tables_missing(client):
    # symulujemy brak bazy
    if TEST_DB.exists():
        TEST_DB.unlink()

    response = client.get("/trophies")

    assert response.status_code == 400
    assert "Brak danych" in response.text



