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

