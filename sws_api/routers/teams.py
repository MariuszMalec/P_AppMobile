from fastapi import APIRouter, Request, Form, Depends, HTTPException, Body, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from starlette.status import HTTP_303_SEE_OTHER
from typing import List, Dict
from templates import templates
from db import get_db
import sqlite3
from urllib.parse import urlencode


router = APIRouter(
    prefix="/teams",
    tags=["teams"]
)


@router.get("", response_class=HTMLResponse)
def teams_page(
    request: Request,
    filter_name: str = Query(None),
    filter_trophy: str = Query(None),
    filter_result: str = Query(None),
    sort: str = Query(None),
    db=Depends(get_db)
):
    try:
        cursor = db.cursor()

        base_query = """
            SELECT
                Teams.*,
                Trophies.Picture AS TrophyPicture,
                Trophies.Name AS TrophyName
            FROM Teams
            LEFT JOIN Trophies
                ON Trophies.Id = Teams.TrophyModelId
        """

        filters = []
        params = []

        # 🔎 Filter by name
        if filter_name and filter_name.strip():
            filters.append("Teams.Name LIKE ?")
            params.append(f"%{filter_name.strip()}%")

        # 🏆 Filter by TrophyWin
        if filter_trophy and filter_trophy.strip():
            filters.append("Teams.TrophyWin LIKE ?")
            params.append(f"%{filter_trophy.strip()}%")

        # ⚽ Filter by Final Result
        if filter_result and filter_result.strip():
            filters.append("Teams.FinalResult LIKE ?")
            params.append(f"%{filter_result.strip()}%")

        if filters:
            base_query += " WHERE " + " AND ".join(filters)

        if sort == "name_asc":
            base_query += " ORDER BY Teams.Name ASC, Teams.Season ASC"

        elif sort == "name_desc":
            base_query += " ORDER BY Teams.Name DESC, Teams.Season DESC"

        elif sort == "season_asc":
            base_query += " ORDER BY Teams.Season ASC, Teams.Name ASC"

        elif sort == "season_desc":
            base_query += " ORDER BY Teams.Season DESC, Teams.Name ASC"

        else:
            base_query += " ORDER BY Teams.Name ASC, Teams.Season ASC"

        teams = cursor.execute(
            base_query,
            params
        ).fetchall()

        return templates.TemplateResponse(
            request,
            "teams.html",
            {
                "teams": teams,
                "filter_name": filter_name,
                "filter_trophy": filter_trophy,
                "filter_result": filter_result,
                "sort": sort
            }
        )

    except sqlite3.OperationalError as e:
        # Brak tabeli Teams/Trophies = brak danych/bazy
        if "no such table" in str(e):
            return templates.TemplateResponse(
                request,
                "teams.html",
                {
                    "teams": [],
                    "filter_name": filter_name,
                    "filter_trophy": filter_trophy,
                    "filter_result": filter_result,
                    "sort": sort,
                    "error": "Brak danych"
                },
                status_code=400
            )

        raise

    finally:
        db.close()


@router.post("/bulk")
def create_teams_bulk(teams: List[Dict] = Body(...), db=Depends(get_db)):

    if not teams:
        raise HTTPException(status_code=400, detail="Empty teams list")

    try:
        cursor = db.cursor()

        for t in teams:
            if not t.get("Name") or not str(t["Name"]).strip():
                raise HTTPException(status_code=400, detail="Team name cannot be empty")

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

    return {"inserted": len(teams), "status": "ok"}


# =============================
# GET TEAM TROPHIES BY SEASON
# =============================
@router.get("/{team_id}/trophies_by_season")
def get_team_trophies_by_season(team_id: int, db=Depends(get_db)):

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
        SELECT Season, TrophyModelId, TrophyWin, FinalResult
        FROM Teams
        WHERE Name = ?
        """,
        (team_name,)
    ).fetchall()

    season_map: Dict[int, List[dict]] = {}

    # tworzymy sezony
    for r in records:
        season_map.setdefault(r["Season"], [])

    # uzupełniamy trofea
    for r in records:

        if not r["TrophyModelId"]:
            continue

        trophy = cursor.execute(
            "SELECT * FROM Trophies WHERE Id = ?",
            (r["TrophyModelId"],)
        ).fetchone()

        if not trophy:
            continue

        result = r["FinalResult"] or ""
        result_lower = result.lower()

        # Domyślnie wygrana tylko wtedy,
        # gdy nie stwierdzimy przegranej.
        lose = False

        # Winner = wygrana
        if "winner" in result_lower:
            lose = False

        # round / 2rd / brak wyniku = przegrana
        elif "round" in result_lower or ":" not in result:
            lose = True

        else:
            try:
                import re

                # Rzuty karne
                pen_match = re.search(
                    r"\(PEN\s+(\d+):(\d+)\)",
                    result,
                    re.IGNORECASE
                )

                if pen_match:
                    pen_a = int(pen_match.group(1))
                    pen_b = int(pen_match.group(2))

                    teams_part = result.split()[0]
                    team_a, team_b = teams_part.split(":", 1)

                    if team_name.strip().lower() == team_a.strip().lower():
                        lose = pen_a < pen_b
                    elif team_name.strip().lower() == team_b.strip().lower():
                        lose = pen_b < pen_a

                else:
                    # Zwykły wynik
                    match = re.search(
                        r"(.+):(.+?)\s+(\d+):(\d+)",
                        result
                    )

                    if match:
                        team_a = match.group(1).strip()
                        team_b = match.group(2).strip()
                        score_a = int(match.group(3))
                        score_b = int(match.group(4))

                        if team_name.strip().lower() == team_a.lower():
                            lose = score_a < score_b

                        elif team_name.strip().lower() == team_b.lower():
                            lose = score_b < score_a

            except Exception:
                lose = False

        season_map[r["Season"]].append({
            "TeamName": team_name,
            "Id": trophy["Id"],
            "Name": trophy["Name"],
            "Picture": trophy["Picture"],
            "Description": trophy["Description"],
            "TrophyWin": r["TrophyWin"],
            "Lose": lose
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
