import sys
from pathlib import Path
from freezegun import freeze_time


import sqlite3
from pathlib import Path

from conftest import TEST_DB



def test_home_page_return_status_code_200(client):
    response = client.get("/home")
    assert response.status_code == 200



