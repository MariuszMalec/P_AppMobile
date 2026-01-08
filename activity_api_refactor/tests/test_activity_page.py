import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_activities_page_page_return_status_code_200():
    response = client.get("/activities")
    assert response.status_code == 200

def test_activities_page_works_with_empty_db(client, empty_db):
    response = client.get("/activities")
    assert response.status_code == 200

def test_activities_page_returns_html():
    response = client.get("/activities")
    assert "text/html" in response.headers["content-type"]

def test_activities_page_contains_day_name():
    response = client.get("/activities")
    assert "Poniedziałek" in response.text or "Wtorek" in response.text


def test_add_activity_return_Status_code_303(client):
    response = client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "20:10",
            "end": "20:15",
            "description": "",
            "person_id": 1,
            "activity_name": "Test"
        },
        follow_redirects=False
    )

    assert response.status_code == 303

