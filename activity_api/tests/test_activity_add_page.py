import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)



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
            "activity_name": "Test",
        },
        follow_redirects=False,
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


def test_add_activity_validation_error(monkeypatch):
    from routers.activity import add_activity_post

    # --- fake validate_activity_form ---
    def fake_validate(*args, **kwargs):
        return ["Błąd formularza"], None

    monkeypatch.setattr(
        "routers.activity.validate_activity_form",
        fake_validate
    )

    # --- fake DB ---
    class FakeCursor:
        def execute(self, sql, params=None):
            if "FROM PictureActivities" in sql:
                self._data = [
                    {"Id": 1, "Name": "Test"}
                ]
            elif "FROM PersonFamilies" in sql:
                self._data = [
                    {"Id": 1, "PersonName": "TATA"},
                    {"Id": 2, "PersonName": "MAMA"},
                    {"Id": 3, "PersonName": "GOSIA"},
                    {"Id": 4, "PersonName": "EMILKA"},
                    {"Id": 5, "PersonName": "RODZINA"},
                ]
            else:
                self._data = []

            return self

        def fetchall(self):
            return self._data

    class FakeDB:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    fake_db = FakeDB()

    captured = {}

    from templates import templates

    def fake_template_response(
        request,
        name,
        context,
        status_code=200
    ):
        captured["name"] = name
        captured["context"] = context
        captured["status"] = status_code

        return {
            "_template": name,
            "_context": context
        }

    monkeypatch.setattr(
        templates,
        "TemplateResponse",
        fake_template_response
    )

    # --- wywołanie metody ---
    result = add_activity_post(
        request=None,
        start="10:00",
        end="11:00",
        day_of_week=2,
        description="",
        person_id=1,
        activity_name="Test",
        db=fake_db,
    )

    # --- asercje ---
    assert captured["name"] == "activity_add.html"
    assert captured["status"] == 400
    assert "errors" in captured["context"]
    assert captured["context"]["errors"] == ["Błąd formularza"]
    assert "activities" in captured["context"]
    

def test_add_activity_success_redirect(monkeypatch):
    from routers.activity import add_activity_post

    # --- fake validate_activity_form ---
    def fake_validate(*args, **kwargs):
        return [], 1  # brak błędów, mamy picture_id

    monkeypatch.setattr(
        "routers.activity.validate_activity_form",
        fake_validate
    )

    # --- fake DB ---
    class FakeCursor:
        def execute(self, sql, params=None):
            if "FROM PictureActivities" in sql:
                self._data = [{"Id": 1, "Name": "Test"}]
            return self

        def fetchall(self):
            return getattr(self, "_data", [])

    class FakeDB:
        def cursor(self):
            return FakeCursor()
        def commit(self):
            pass
        def close(self):
            pass

    fake_db = FakeDB()

    result = add_activity_post(
        request=None,
        start="08:00",
        end="09:00",
        day_of_week=2,
        description="",
        person_id=1,
        activity_name="Test",
        db=fake_db,
    )

    # sukces = redirect
    assert result.status_code == 303

    assert result.headers["location"] == "/live/liveall/2"


def test_add_activity_invalid_time_range(monkeypatch):
    from routers.activity import add_activity_post
    from templates import templates

    # --- fake validate_activity_form ---
    def fake_validate(*args, **kwargs):
        return ["Start musi być < End"], None

    # 🔴 patch w MIEJSCU UŻYCIA
    monkeypatch.setattr(
        "routers.activity.validate_activity_form",
        fake_validate
    )

    class FakeDB:
        def cursor(self): return self
        def execute(self, *a, **k): return self
        def fetchall(self): return []
        def close(self): pass

    captured = {}

    original = templates.TemplateResponse

    def fake_template_response(request, name, context, status_code=200):
        captured["name"] = name
        captured["context"] = context
        captured["status"] = status_code
        return {"_template": name, "_context": context}

    monkeypatch.setattr(templates, "TemplateResponse", fake_template_response)

    result = add_activity_post(
        request=None,
        start="09:00",
        end="10:00",
        day_of_week=2,
        description="",
        person_id=1,
        activity_name="Test",
        db=FakeDB(),
    )

    assert captured["status"] == 400
    assert "errors" in captured["context"]
    assert captured["context"]["errors"] == ["Start musi być < End"]



