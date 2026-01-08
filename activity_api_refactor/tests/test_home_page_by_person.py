import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_home_by_person_return_status_code_200():
    response = client.get(
        "/home/homebyperson",
        params={"person": "MAMA"}
    )

    assert response.status_code == 200
