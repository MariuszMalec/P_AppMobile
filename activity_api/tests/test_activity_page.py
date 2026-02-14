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

