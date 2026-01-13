from fastapi import FastAPI, HTTPException
from typing import List, Dict
from database import get_db


app = FastAPI()

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
            "Season": season,
            "Trophies": trophies
        }
        for season, trophies in sorted(season_map.items())
    ]