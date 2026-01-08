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

def test_activities_page_multiple_days_rendered():
    response = client.get("/activities")
    assert any(day in response.text for day in ["Poniedziałek", "Wtorek", "Środa"])


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


def test_add_activity_return_Status_code_400(client):
    response = client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "20:10",
            "end": "20:10",
            "description": "",
            "person_id": 1,
            "activity_name": "Test"
        },
        follow_redirects=False
    )
    assert response.status_code == 400


def test_add_activity_return_Status_code_400(client):
    response = client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "20:10",
            "end": "20:05",
            "description": "",
            "person_id": 1,
            "activity_name": "Test"
        },
        follow_redirects=False
    )
    assert response.status_code == 400


def test_add_activity_return_Status_code_303(client):
    response = client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "23:10",
            "end": "00:05",
            "description": "",
            "person_id": 1,
            "activity_name": "Test"
        },
        follow_redirects=False
    )
    assert response.status_code == 303


def test_edit_activity_return_303():
    response = client.post(
        "/activities/edit/1",
        data={
            "day_of_week": 1,
            "start": "21:00",
            "end": "21:30",
            "description": "EDIT",
            "person_id": 1,
            "picture_id": 1
        },
        follow_redirects=False
    )

    assert response.status_code == 303


def test_edit_activity_not_found_returns_404():
    response = client.post(
        "/activities/edit/99999",
        data={
            "day_of_week": 1,
            "start": "10:00",
            "end": "10:30",
            "description": "",
            "person_id": 1,
            "picture_id": 1
        }
    )

    assert response.status_code == 404


def test_edit_activity_invalid_time_start_later_than_end_returns_400():
    response = client.post(
        "/activities/edit/1",
        data={
            "day_of_week": 1,
            "start": "22:00",
            "end": "21:00",  # ❌
            "description": "",
            "person_id": 1,
            "picture_id": 1
        }
    )

    assert response.status_code == 400


def test_edit_activity_time_conflict_activity_exist_yet_returns_400():
    response = client.post(
        "/activities/edit/1",
        data={
            "day_of_week": 1,
            "start": "20:00",
            "end": "21:00",
            "description": "",
            "person_id": 1,
            "picture_id": 1
        }
    )

    assert response.status_code == 400
    assert "Masz już zaplanowaną aktywność" in response.text

def test_edit_activity_time_conflict_start_thesame_as_end_returns_400():
    response = client.post(
        "/activities/edit/1",
        data={
            "day_of_week": 1,
            "start": "20:00",
            "end": "20:00",
            "description": "",
            "person_id": 1,
            "picture_id": 1
        }
    )

    assert response.status_code == 400
    assert "Godzina startu musi być inna niż zakończenia" in response.text


