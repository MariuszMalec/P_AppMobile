import sys
from pathlib import Path
from freezegun import freeze_time


import sqlite3
from pathlib import Path

from conftest import TEST_DB


def test_home_page_return_status_code_200(client):
    response = client.get("/home")
    assert response.status_code == 200

def test_home_works_with_empty_db(client, empty_db):
    response = client.get("/home")

    assert response.status_code == 200
    assert "no-data" in response.text  # np. klasa w HTML


def test_home_works_when_tables_missing(client):
    # symulujemy brak bazy
    if TEST_DB.exists():
        TEST_DB.unlink()

    response = client.get("/home")

    assert response.status_code == 400
    assert "Brak danych" in response.text



def test_home_context_keys(client):
    response = client.get("/home")
    ctx = response.context

    assert "current_day_name" in ctx
    

def test_home_by_person_return_status_code_200(client):
    response = client.get(
        "/home/homebyperson",
        params={"person": "MAMA"}
    )
    assert response.status_code == 200


def test_home_by_person_invalid_person_fallback(client):
    response = client.get(
        "/home/homebyperson",
        params={"person": "XXX"}
    )
    assert response.status_code == 200



