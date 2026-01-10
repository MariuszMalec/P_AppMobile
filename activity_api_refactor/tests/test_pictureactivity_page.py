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
