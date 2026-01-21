from fastapi import APIRouter, Request, Form, Depends, HTTPException, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from starlette.status import HTTP_303_SEE_OTHER
import sqlite3
from typing import List, Dict
from templates import templates

from db import get_db



router = APIRouter(
    prefix="/teams",
    tags=["teams"]
)

@router.get("", response_class=HTMLResponse)
def teams_page(request: Request, db = Depends(get_db)):

    cursor = db.cursor()

    teams = cursor.execute("""
        SELECT
            Teams.*,
            Trophies.Picture AS TrophyPicture,
            Trophies.Name AS TrophyName
        FROM Teams
        LEFT JOIN Trophies
            ON Trophies.Id = Teams.TrophyModelId
    """).fetchall()
    db.close()

    return templates.TemplateResponse(
        "teams.html",
        {
            "request": request,
            "teams": teams
        }
    )


@router.post("/bulk", response_class=HTMLResponse)
def create_teams_bulk(teams: List[Dict] = Body(...),db = Depends(get_db)):

    if not teams:
        raise HTTPException(status_code=400, detail="Empty teams list")   

    try:
        for t in teams:
            if not t.get("Name") or not str(t["Name"]).strip():
                raise HTTPException(status_code=400, detail="Team name cannot be empty")

            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO Teams
                (Name, Description, NationalityName, Season, TopScorer,
                 Picture, FinalResult, TrophyWin, TrophyModelId)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    t.get("Name"),
                    t.get("Description"),
                    t.get("NationalityName"),
                    t.get("Season"),
                    t.get("TopScorer"),
                    t.get("Picture"),
                    t.get("FinalResult"),
                    t.get("TrophyWin"),
                    t.get("TrophyModelId"),
                )
            )

        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    return {
        "inserted": len(teams),
        "status": "ok"
    }