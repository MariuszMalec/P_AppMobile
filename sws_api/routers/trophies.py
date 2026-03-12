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

# ==============================
# EDIT TROPHY - FORM
# ==============================

@router.get("/edit/{trophy_id}", response_class=HTMLResponse)
def edit_trophy_page(
    request: Request,
    trophy_id: int,
    db = Depends(get_db)
):
    cursor = db.cursor()

    trophy = cursor.execute("""
        SELECT * FROM Trophies WHERE Id = ?
    """, (trophy_id,)).fetchone()

    teams = cursor.execute("""
        SELECT * FROM Teams
    """).fetchall()

    db.close()

    return templates.TemplateResponse(
        "trophy_edit.html",
        {
            "request": request,
            "trophy": trophy,
            "teams": teams
        }
    )


# ==============================
# EDIT TROPHY - SAVE
# ==============================

from typing import Optional

@router.post("/edit/{trophy_id}")
def edit_trophy(
    trophy_id: int,
    Name: str = Form(...),
    Description: str = Form(...),
    Picture: str = Form(...),
    TeamModelId: Optional[int] = Form(None),
    db = Depends(get_db)
):

    cursor = db.cursor()

    cursor.execute("""
        UPDATE Trophies
        SET Name=?, Description=?, Picture=?, TeamModelId=?
        WHERE Id=?
    """, (Name, Description, Picture, TeamModelId, trophy_id))

    db.commit()
    db.close()

    return RedirectResponse(
        url="/trophies",
        status_code=303
    )
