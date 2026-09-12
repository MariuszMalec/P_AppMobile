from datetime import datetime

import sqlite3
from pathlib import Path

from conftest import TEST_DB


def freeze_time(monkeypatch, fake_dt: datetime):
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fake_dt

    import routers.livenow as mod
    monkeypatch.setattr(mod, "datetime", FakeDatetime)


def test_livenow_page_return_status_code_200(client):
    response = client.get("/live/now")
    assert response.status_code == 200


def test_livenow_page_works_with_empty_db(client, empty_db):
    response = client.get("/live/now")
    assert response.status_code == 200


def test_livenow_shows_current_activity(client, monkeypatch):
    fake_now = datetime(2026, 1, 5, 19, 45, 0)
    freeze_time(monkeypatch, fake_now)

    client.post(
        "/activities/add",
        data={
            "day_of_week": 2,
            "start": "19:30",
            "end": "20:30",
            "description": "LIVE TEST",
            "person_id": 2,
            "activity_name": "Test",
        },
        follow_redirects=False
    )

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT DayOfWeek, StartTime, EndTime, Description FROM ActiviesDays"
    ).fetchall()
    conn.close()

    live_rows = [dict(r) for r in rows if r["Description"] == "LIVE TEST"]
    assert len(live_rows) == 1

    response = client.get("/live/now")
    assert response.status_code == 200
    assert "LIVE TEST" in response.text



def test_livenow_does_not_show_outside_time(client, monkeypatch, empty_db):
    # Zamrażamy czas: poniedziałek 18:00 (poza zakresem)
    fake_now = datetime(2026, 1, 5, 18, 0, 0)
    freeze_time(monkeypatch, fake_now)

    client.post(
        "/activities/add",
        data={
            "day_of_week": 1,
            "start": "19:30",
            "end": "20:30",
            "description": "SHOULD NOT BE LIVE",
            "person_id": 2,
            "activity_name": "Pranie",
        },
        follow_redirects=False
    )

    response = client.get("/live/now")

    assert response.status_code == 200
    assert "SHOULD NOT BE LIVE" not in response.text
