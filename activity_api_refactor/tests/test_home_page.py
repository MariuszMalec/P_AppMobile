import sys
from pathlib import Path
from freezegun import freeze_time

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@freeze_time("2025-01-08 20:10:00")
def test_home_current_and_next_items(client):
    response = client.get("/home")
    ctx = response.context

    assert len(ctx["current"]) >= 0
    assert all(
        item["start"] <= ctx["now"] <= item["end"]
        for item in ctx["current"]
    )



def test_home_page_return_status_code_200():
    response = client.get("/")
    assert response.status_code == 200

def test_home_works_with_empty_db(client, empty_db):
    response = client.get("/home")
    assert response.status_code == 200

def test_home_context_keys(client):
    response = client.get("/home")
    ctx = response.context

    assert "now" in ctx
    assert "current" in ctx
    assert "next" in ctx
    assert "current_day_name" in ctx
    

def test_home_by_person_return_status_code_200():
    response = client.get(
        "/home/homebyperson",
        params={"person": "MAMA"}
    )
    assert response.status_code == 200


def test_home_by_person_all_status_200():
    response = client.get(
        "/home/homebyperson",
        params={"person": "ALL"}
    )
    assert response.status_code == 200

def test_home_by_person_invalid_person_fallback():
    response = client.get(
        "/home/homebyperson",
        params={"person": "XXX"}
    )
    assert response.status_code == 200

def test_home_by_person_empty_db_status_200():
    response = client.get("/home/homebyperson")
    assert response.status_code == 200



