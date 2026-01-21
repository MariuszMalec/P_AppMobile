from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from templates import templates
from db import get_db


router = APIRouter(
    prefix="/trophies",
    tags=["trophies"]
)


# ==============================
# LISTA PICTURE Trophies
# ==============================

@router.get("", response_class=HTMLResponse)
def trophies_page(request: Request,
    db = Depends(get_db)):

    cursor = db.cursor()

    trophies = cursor.execute("""
        SELECT Trophies.*, Teams.Name AS TeamName
        FROM Trophies
        LEFT JOIN Teams ON Teams.Id = Trophies.TeamModelId
    """).fetchall()
    db.close()

    return templates.TemplateResponse(
        "trophies.html",
        {
            "request": request,
            "trophies": trophies
        }
    )

