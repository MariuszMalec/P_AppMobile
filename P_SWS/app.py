from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from typing import List

from database import get_db
from init_db import init_db

# =============================
# APP + TEMPLATES
# =============================
app = FastAPI()
templates = Jinja2Templates(directory="templates")


# =============================
# AUTO INIT DB ON STARTUP
# =============================
@app.on_event("startup")
def on_startup():
    init_db()


# =============================
# API – TEAMS (JSON)
# =============================
@app.get("/teams")
def get_teams():
    db = get_db()
    rows = db.execute("SELECT * FROM Teams").fetchall()
    db.close()
    return [dict(r) for r in rows]


@app.post("/teams/bulk")
def create_teams_bulk(teams: List[dict]):
    if not teams:
        raise HTTPException(400, "Empty teams list")

    db = get_db()

    try:
        for t in teams:
            if not t.get("Name") or not t["Name"].strip():
                raise HTTPException(400, "Team name cannot be empty")

            db.execute(
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
        raise HTTPException(500, str(e))
    finally:
        db.close()

    return {"inserted": len(teams), "status": "ok"}


# =============================
# API – TROPHIES (JSON)
# =============================
@app.get("/trophies")
def get_trophies():
    db = get_db()
    rows = db.execute("SELECT * FROM Trophies").fetchall()
    db.close()
    return [dict(r) for r in rows]


@app.post("/trophies/bulk")
def create_trophies_bulk(trophies: List[dict]):
    if not trophies:
        raise HTTPException(400, "Empty trophies list")

    db = get_db()

    try:
        for t in trophies:
            if not t.get("Name") or not t["Name"].strip():
                raise HTTPException(400, "Trophy name cannot be empty")

            team_id = t.get("TeamModelId")
            if team_id is not None:
                team = db.execute(
                    "SELECT 1 FROM Teams WHERE Id = ?",
                    (team_id,)
                ).fetchone()

                if not team:
                    raise HTTPException(404, f"Team {team_id} not found")

            db.execute(
                """
                INSERT INTO Trophies
                (Name, Description, Picture, TeamModelId)
                VALUES (?, ?, ?, ?)
                """,
                (
                    t.get("Name"),
                    t.get("Description"),
                    t.get("Picture"),
                    team_id
                )
            )

        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()

    return {"inserted": len(trophies), "status": "ok"}


# =============================
# UI – TEAMS (HTML)
# =============================
@app.get("/")
def teams_page(request: Request):
    db = get_db()
    teams = db.execute("""
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


@app.get("/ui/teams")
def teams_page(request: Request):
    db = get_db()
    teams = db.execute("""
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

# =============================
# UI – TROPHIES (HTML)
# =============================
@app.get("/ui/trophies")
def trophies_page(request: Request):
    db = get_db()
    trophies = db.execute("""
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
