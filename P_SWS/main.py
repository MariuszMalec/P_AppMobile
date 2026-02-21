from fastapi import FastAPI, HTTPException
from typing import List, Dict
from database import get_db
from fastapi.staticfiles import StaticFiles
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

# =============================
# GET TEAMS
# =============================
@app.get("/teams")
def get_teams():
    db = get_db()
    rows = db.execute("SELECT * FROM Teams").fetchall()
    db.close()
    return [dict(r) for r in rows]


# =============================
# GET TEAM BY ID
# =============================
@app.get("/teams/{team_id}")
def get_team(team_id: int):
    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM Teams WHERE id = ?",
            (team_id,)
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Team with id {team_id} not found"
            )

        return dict(row)

    finally:
        db.close()

# =============================
# BULK POST TEAMS
# =============================
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

    return {
        "inserted": len(teams),
        "status": "ok"
    }


# =============================
# GET TROPHIES
# =============================
@app.get("/trophies")
def get_trophies():
    db = get_db()
    rows = db.execute("SELECT * FROM Trophies").fetchall()
    db.close()
    return [dict(r) for r in rows]


# =============================
# BULK POST TROPHIES
# =============================
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
                INSERT INTO Trophies (Name, Description, Picture, TeamModelId)
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

    return {
        "inserted": len(trophies),
        "status": "ok"
    }



# =============================
# GET TEAM TROPHIES BY SEASON
# =============================
@app.get("/teams/{team_id}/trophies_by_season")
def get_team_trophies_by_season(team_id: int):
    db = get_db()

    team = db.execute(
        "SELECT * FROM Teams WHERE Id = ?",
        (team_id,)
    ).fetchone()

    if not team:
        db.close()
        raise HTTPException(404, "Team not found")

    team_name = team["Name"]

    records = db.execute(
        "SELECT Season, TrophyModelId FROM Teams WHERE Name = ?",
        (team_name,)
    ).fetchall()

    season_map: Dict[int, List[dict]] = {}

    # najpierw tworzymy wszystkie sezony
    for r in records:
        season_map.setdefault(r["Season"], [])

    # potem uzupełniamy trofea
    for r in records:
        if r["TrophyModelId"]:
            trophy = db.execute(
                "SELECT * FROM Trophies WHERE Id = ?",
                (r["TrophyModelId"],)
            ).fetchone()

            if trophy:
                season_map[r["Season"]].append({
                    "TeamName": team_name,
                    "Id": trophy["Id"],
                    "Name": trophy["Name"],
                    "Picture": trophy["Picture"],
                    "Description": trophy["Description"]
                })

    db.close()

    return [
        {
            "TeamName": team_name,
            "Season": season,
            "Trophies": trophies
        }
        for season, trophies in sorted(season_map.items())
    ]

# =============================
# CREATE SINGLE TEAM
# =============================
@app.post("/teams")
def create_team(team: dict):

    if not team.get("Name") or not team["Name"].strip():
        raise HTTPException(400, "Team name cannot be empty")

    db = get_db()

    try:
        # opcjonalna walidacja TrophyModelId
        trophy_id = team.get("TrophyModelId")
        if trophy_id is not None:
            trophy = db.execute(
                "SELECT 1 FROM Trophies WHERE Id = ?",
                (trophy_id,)
            ).fetchone()

            if not trophy:
                raise HTTPException(404, f"Trophy {trophy_id} not found")

        cursor = db.execute(
            """
            INSERT INTO Teams
            (Name, Description, NationalityName, Season, TopScorer,
             Picture, FinalResult, TrophyWin, TrophyModelId)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                team.get("Name"),
                team.get("Description"),
                team.get("NationalityName"),
                team.get("Season"),
                team.get("TopScorer"),
                team.get("Picture"),
                team.get("FinalResult"),
                team.get("TrophyWin"),
                trophy_id,
            )
        )

        db.commit()

        new_id = cursor.lastrowid

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

    finally:
        db.close()

    return {
        "id": new_id,
        "status": "created"
    }

# =============================
# DELETE TEAM
# =============================
@app.delete("/teams/{team_id}")
def delete_team(team_id: int):

    db = get_db()

    try:
        # sprawdź czy istnieje
        team = db.execute(
            "SELECT * FROM Teams WHERE Id = ?",
            (team_id,)
        ).fetchone()

        if not team:
            raise HTTPException(404, f"Team with id {team_id} not found")

        # opcjonalnie: wyczyść powiązania w Trophies (jeśli istnieją)
        db.execute(
            "UPDATE Trophies SET TeamModelId = NULL WHERE TeamModelId = ?",
            (team_id,)
        )

        # usuń team
        db.execute(
            "DELETE FROM Teams WHERE Id = ?",
            (team_id,)
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

    return {
        "id": team_id,
        "status": "deleted"
    }
