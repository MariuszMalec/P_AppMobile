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


# =============================
# GET TEAM TROPHIES BY SEASON
# =============================
@router.get("/{team_id}/trophies_by_season/")
def get_team_trophies_by_season(
    team_id: int,
    request: Request,
    db = Depends(get_db)
):
    cursor = db.cursor()

    team = cursor.execute(
        "SELECT * FROM Teams WHERE Id = ?",
        (team_id,)
    ).fetchone()

    if not team:
        db.close()
        raise HTTPException(404, "Team not found")

    team_name = team["Name"]

    records = cursor.execute(
        """
        SELECT DISTINCT Season, TrophyModelId
        FROM Teams
        WHERE Name = ?
        """,
        (team_name,)
    ).fetchall()

    season_map: Dict[int, List[dict]] = {}

    for r in records:
        season_map.setdefault(r["Season"], [])

    for r in records:
        if r["TrophyModelId"]:
            trophy = cursor.execute(
                "SELECT * FROM Trophies WHERE Id = ?",
                (r["TrophyModelId"],)
            ).fetchone()

            if trophy:
                season_map[r["Season"]].append({
                    "Id": trophy["Id"],
                    "Name": trophy["Name"],
                    "Picture": trophy["Picture"],
                    "Description": trophy["Description"]
                })

    db.close()

    seasons = [
        {
            "Season": season,
            "Trophies": trophies
        }
        for season, trophies in sorted(season_map.items())
    ]

    return templates.TemplateResponse(
        "trophies_by_season.html",
        {
            "request": request,
            "team_name": team_name,
            "seasons": seasons
        }
    )


# =============================
# GET TEAM PICTURE
# =============================
@router.get("/{team_id}/picture", response_class=JSONResponse)
def get_team_picture(team_id: int, db = Depends(get_db)):
    cursor = db.cursor()

    team = cursor.execute(
        "SELECT Picture FROM Teams WHERE Id = ?",
        (team_id,)
    ).fetchone()

    db.close()

    if not team or not team["Picture"]:
        raise HTTPException(status_code=404, detail="Picture not found")

    return {
        "picture": team["Picture"]
    }
