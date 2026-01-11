import sqlite3
from pathlib import Path

from conftest import TEST_DB


def test_pictureactivities_page_return_status_code_200(client):
    response = client.get("/pictureactivities")
    assert response.status_code == 200

def test_pictureactivities_works_with_empty_db(client, empty_db):
    response = client.get("/pictureactivities")
    assert response.status_code == 200


def test_picture_activities_page_items_context(client, monkeypatch):
    import sqlite3

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO PictureActivities (Name, ActivityName, Picture)
        VALUES (?, ?, ?)
        """,
        ("Test", "Test", "/img/test.png")
    )
    conn.commit()
    conn.close()

    captured = {}

    from templates import templates
    original = templates.TemplateResponse

    def fake_template_response(request, name, context):
        captured["name"] = name
        captured["context"] = context
        return original(request, name, context)

    monkeypatch.setattr(templates, "TemplateResponse", fake_template_response)

    response = client.get("/pictureactivities")
    assert response.status_code == 200

    items = captured["context"]["items"]
    
    assert any(i["activityName"] == "Test" for i in items)



def test_picture_activities_page_builds_items(monkeypatch):
    from routers.pictureactivity import picture_activities_page

    # --- fake DB ---
    class FakeCursor:
        def execute(self, sql):
            return self
        def fetchall(self):
            return [
                {"Id": 1, "Name": "Test", "Picture": "/img/test.png"},
                {"Id": 2, "Name": "ABC",  "Picture": "/img/abc.png"},
            ]

    class FakeDB:
        def cursor(self):
            return FakeCursor()
        def close(self):
            pass

    fake_db = FakeDB()

    captured = {}

    # --- przechwyć TemplateResponse ---
    from templates import templates
    original = templates.TemplateResponse

    def fake_template_response(request, name, context):
        captured["name"] = name
        captured["context"] = context
        return {"_template": name, "_context": context}

    monkeypatch.setattr(templates, "TemplateResponse", fake_template_response)

    # --- wywołanie funkcji bez HTTP ---
    result = picture_activities_page(request=None, db=fake_db)

    items = captured["context"]["items"]

    assert items == [
        {"id": 1, "activityName": "Test", "picture": "/img/test.png"},
        {"id": 2, "activityName": "ABC",  "picture": "/img/abc.png"},
    ]


def test_add_activity_validation_error(monkeypatch):
    from routers.activity import add_activity_post

    # --- fake validate_activity_form ---
    def fake_validate(*args, **kwargs):
        return ["Błąd formularza"]

    # 🔴 patch w MIEJSCU UŻYCIA
    monkeypatch.setattr(
        "routers.activity.validate_activity_form",
        fake_validate
    )

    # --- fake DB ---
    class FakeCursor:
        def execute(self, sql, params=None):
            # tylko lista aktywności (pierwsze SELECT)
            self._data = [{"Id": 1, "Name": "Test"}]
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

    def fake_template_response(request, name, context, status_code=200):
        captured["name"] = name
        captured["context"] = context
        captured["status"] = status_code
        return {"_template": name, "_context": context}

    monkeypatch.setattr(templates, "TemplateResponse", fake_template_response)

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

    # validate zwraca brak błędów
    monkeypatch.setattr(
        "routers.activity.validate_activity_form",
        lambda *a, **k: []
    )

    # --- fake DB ---
    class FakeCursor:
        def execute(self, sql, params=None):
            if "SELECT Id FROM PictureActivities" in sql:
                self._one = {"Id": 1}
            elif "FROM PictureActivities" in sql:
                self._data = [{"Id": 1, "Name": "Test"}]
            elif "FROM ActiviesDays" in sql:
                self._data = []  # brak konfliktów
            return self

        def fetchall(self):
            return getattr(self, "_data", [])

        def fetchone(self):
            return getattr(self, "_one", None)


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
        start="11:00",
        end="12:00",
        day_of_week=2,
        description="",
        person_id=1,
        activity_name="Test",
        db=fake_db,
    )

    # sukces = redirect
    assert result.status_code == 303
    assert result.headers["location"] == "/activities"


def test_add_activity_invalid_time_range(monkeypatch):
    from routers.activity import add_activity_post
    from templates import templates

    # walidator zawsze zwraca błąd
    monkeypatch.setattr(
        "routers.activity.validate_activity_form",
        lambda *a, **k: ["Start musi być < End"]
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
        start="11:00",
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


def test_add_activity_invalid_time_startendthesame(monkeypatch):
    from routers.activity import add_activity_post
    from templates import templates

    # walidator zawsze zwraca błąd
    monkeypatch.setattr(
        "routers.activity.validate_activity_form",
        lambda *a, **k: ["Start musi być != End"]
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
        start="10:00",
        end="11:00",
        day_of_week=2,
        description="",
        person_id=1,
        activity_name="Test",
        db=FakeDB(),
    )

    assert captured["status"] == 400
    assert "errors" in captured["context"]
    assert captured["context"]["errors"] == ["Start musi być != End"]