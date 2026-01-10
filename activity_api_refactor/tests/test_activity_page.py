import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_activities_page_page_return_status_code_200(client):
    response = client.get("/activities")
    assert response.status_code == 200

def test_activities_page_works_with_empty_db(client, empty_db):
    response = client.get("/activities")
    assert response.status_code == 200

def test_activities_page_returns_html(client):
    response = client.get("/activities")
    assert "text/html" in response.headers["content-type"]

def test_activities_page_contains_day_name(client):
    response = client.get("/activities")
    assert "Poniedziałek" in response.text or "Wtorek" in response.text

def test_activities_page_multiple_days_rendered(client):
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


def test_add_activity_return_Status_When_StartTimeIsTheSameAsEndTime_code_400(client):
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


def test_add_activity_return_Status_WhenStart_Later_ThenEnd_code_400(client):
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


def test_add_activity_midnight_return_Status_code_303(client):
    response = client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "23:10",
            "end": "00:05",
            "description": "ADD",
            "person_id": 1,
            "activity_name": "Test"
        },
        follow_redirects=False
    )

    # 3️⃣ Próba dodania konfiktowej aktywnosci
    response = client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "00:05",
            "end": "01:00",
            "description": "SHOULD SAVE",
            "person_id": 2,
            "activity_name": "Pranie",
        },
        follow_redirects=False,  # żeby dostać HTML z błędem
    )

    assert response.status_code == 303



def test_add_activity_time_conflict_does_not_update(client):
    # 1️⃣ Pierwsza aktywność
    client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "19:30",
            "end": "20:30",
            "description": "EXISTING",
            "person_id": 2,
            "activity_name": "Pranie",  # <- prawdziwa nazwa z PictureActivities
        },
        follow_redirects=True,
    )

    # 3️⃣ Próba dodania konfiktowej aktywnosci
    response = client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "19:45",
            "end": "21:00",
            "description": "SHOULD NOT SAVE",
            "person_id": 2,
            "activity_name": "Pranie",
        },
        follow_redirects=True,  # żeby dostać HTML z błędem
    )

    assert response.status_code == 400
    #assert "aktywność w tym czasie" in response.text

    errors = response.context["errors"]

    assert len(errors) == 1
    assert "Masz już zaplanowaną aktywność w tym czasie" in errors[0]


    page = client.get("/activities")
    assert "SHOULD NOT SAVE" not in page.text



def test_edit_activity_return_303(client):

    # 1️⃣ Pierwsza aktywność
    client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "19:30",
            "end": "20:30",
            "description": "EXISTING",
            "person_id": 2,
            "activity_name": "Pranie",  # <- prawdziwa nazwa z PictureActivities
        },
        follow_redirects=True,
    )

    response = client.post(
        "/activities/edit/38",
        data={
            "day_of_week": 1,
            "start": "19:30",
            "end": "21:30",
            "description": "EDIT",
            "person_id": 1,
            "picture_id": 1
        },
        follow_redirects=False
    )

    assert response.status_code == 303


def test_edit_activity_not_found_returns_404(client):
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


def test_edit_activity_time_conflict_does_not_update_activity(client):
    # 1️⃣ pierwsza
    r1 = client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "19:30",
            "end": "20:30",
            "description": "EXISTING",
            "person_id": 2,
            "activity_name": "Pranie",
        },
        follow_redirects=True,
    )

    # 2️⃣ druga
    r2 = client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "21:00",
            "end": "22:00",
            "description": "SECOND",
            "person_id": 2,
            "activity_name": "Pranie",
        },
        follow_redirects=True,
    )

    activity_id = 2  # jeśli wiesz, że testowa baza startuje pusta

    # 3️⃣ edycja drugiej – wchodzi w pierwszą
    response = client.post(
        f"/activities/edit/{activity_id}",
        data={
            "day_of_week": 1,
            "start": "20:00",
            "end": "21:15",
            "description": "NOT EDIT",
            "person_id": 2,
            "picture_id": 1,
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "aktywność w tym czasie" in response.text




def test_edit_activity_return_Status_When_StartTimeIsTheSameAsEndTime_code_400(client):
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
    assert "Czas trwania aktywności nie może wynosić 0 minut" in response.text


