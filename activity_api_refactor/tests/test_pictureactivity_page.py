import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)



def test_pictureactivities_page_return_status_code_200():
    response = client.get("/pictureactivities")
    assert response.status_code == 200

def test_pictureactivities_works_with_empty_db(client, empty_db):
    response = client.get("/pictureactivities")
    assert response.status_code == 200