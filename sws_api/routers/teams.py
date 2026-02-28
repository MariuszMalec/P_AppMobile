from fastapi import APIRouter, Request, Form, Depends, HTTPException, Body, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from starlette.status import HTTP_303_SEE_OTHER
from typing import List, Dict
from templates import templates
from db import get_db


router = APIRouter(
    prefix="/teams",
    tags=["teams"]
)


@router.get("", response_class=HTMLResponse)
def teams_page(
    request: Request,
    filter_name: str = Query(None),
    sort: str = Query(None),
    db=Depends(get_db)
):
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

    if filter_name and filter_name.strip():
        filters.append("Teams.Name LIKE ?")
        params.append(f"%{filter_name.strip()}%")

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    if sort == "name_asc":
        base_query += " ORDER BY Teams.Name ASC"
    elif sort == "name_desc":
        base_query += " ORDER BY Teams.Name DESC"

    teams = cursor.execute(base_query, params).fetchall()
    db.close()

    return templates.TemplateResponse(
        "teams.html",
        {
            "request": request,
            "teams": teams,
            "filter_name": filter_name,
            "sort": sort
        }
    )


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


@router.get("/{team_id}/trophies_by_season/", response_class=HTMLResponse)
def get_team_trophies_by_season(
    team_id: int,
    request: Request,
    db=Depends(get_db)
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
        {"Season": season, "Trophies": trophies}
        for season, trophies in sorted(season_map.items())
    ]

    # Pobranie parametrów filtr/sort z query
    filter_name = request.query_params.get("filter_name")
    sort = request.query_params.get("sort")

    query_params = []
    if filter_name:
        query_params.append(f"filter_name={filter_name}")
    if sort:
        query_params.append(f"sort={sort}")

    query_string = "?" + "&".join(query_params) if query_params else ""

    return templates.TemplateResponse(
        "trophies_by_season.html",
        {
            "request": request,
            "team_name": team_name,
            "seasons": seasons,
            "query_string": query_string
        }
    )




@router.get("/{team_id}/picture", response_class=JSONResponse)
def get_team_picture(team_id: int, db=Depends(get_db)):
    cursor = db.cursor()

    team = cursor.execute(
        "SELECT Picture FROM Teams WHERE Id = ?",
        (team_id,)
    ).fetchone()

    db.close()

    if not team or not team["Picture"]:
        raise HTTPException(status_code=404, detail="Picture not found")

    return {"picture": team["Picture"]}


@router.post("/create")
def create_team(
    request: Request,
    Name: str = Form(...),
    Description: str = Form(None),
    NationalityName: str = Form(None),
    Season: int = Form(None),
    TopScorer: str = Form(None),
    Picture: str = Form(None),
    FinalResult: str = Form(None),
    TrophyWin: str = Form(None),
    TrophyModelId: int = Form(None),
    filter_name: str = Form(None),
    sort: str = Form(None),
    db=Depends(get_db)
):
    if not Name.strip():
        raise HTTPException(status_code=400, detail="Team name cannot be empty")

    try:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO Teams
            (Name, Description, NationalityName, Season, TopScorer,
             Picture, FinalResult, TrophyWin, TrophyModelId)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                Name,
                Description,
                NationalityName,
                Season,
                TopScorer,
                Picture,
                FinalResult,
                TrophyWin,
                TrophyModelId
            )
        )
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    redirect_url = "/teams"
    params = []

    if filter_name:
        params.append(f"filter_name={filter_name}")
    if sort:
        params.append(f"sort={sort}")

    if params:
        redirect_url += "?" + "&".join(params)

    return RedirectResponse(url=redirect_url, status_code=HTTP_303_SEE_OTHER)


@router.post("/{team_id}/delete")
def delete_team(
    team_id: int,
    request: Request,
    filter_name: str = Form(None),
    sort: str = Form(None),
    db=Depends(get_db)
):
    try:
        cursor = db.cursor()

        team = cursor.execute(
            "SELECT * FROM Teams WHERE Id = ?",
            (team_id,)
        ).fetchone()

        if not team:
            db.close()
            raise HTTPException(status_code=404, detail="Team not found")

        cursor.execute(
            "DELETE FROM Teams WHERE Id = ?",
            (team_id,)
        )
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    redirect_url = "/teams"
    params = []

    if filter_name:
        params.append(f"filter_name={filter_name}")
    if sort:
        params.append(f"sort={sort}")

    if params:
        redirect_url += "?" + "&".join(params)

    return RedirectResponse(url=redirect_url, status_code=HTTP_303_SEE_OTHER)


@router.get("/{team_id}/edit", response_class=HTMLResponse)
def edit_team_form(team_id: int, request: Request, db=Depends(get_db)):
    cursor = db.cursor()

    team = cursor.execute(
        "SELECT * FROM Teams WHERE Id = ?",
        (team_id,)
    ).fetchone()

    if not team:
        db.close()
        raise HTTPException(status_code=404, detail="Team not found")

    db.close()

    return templates.TemplateResponse(
        "edit_team.html",
        {
            "request": request,
            "team": team,
            "filter_name": request.query_params.get("filter_name"),
            "sort": request.query_params.get("sort")
        }
    )


@router.post("/{team_id}/edit")
def edit_team(
    team_id: int,
    request: Request,
    Name: str = Form(...),
    Description: str = Form(None),
    NationalityName: str = Form(None),
    Season: int = Form(None),
    TopScorer: str = Form(None),
    Picture: str = Form(None),
    FinalResult: str = Form(None),
    TrophyWin: str = Form(None),
    TrophyModelId: int = Form(None),
    filter_name: str = Form(None),
    sort: str = Form(None),
    db=Depends(get_db)
):
    if not Name.strip():
        raise HTTPException(status_code=400, detail="Team name cannot be empty")

    try:
        cursor = db.cursor()

        existing = cursor.execute(
            "SELECT * FROM Teams WHERE Id = ?",
            (team_id,)
        ).fetchone()

        if not existing:
            db.close()
            raise HTTPException(status_code=404, detail="Team not found")

        cursor.execute(
            """
            UPDATE Teams
            SET Name = ?, Description = ?, NationalityName = ?, Season = ?, TopScorer = ?,
                Picture = ?, FinalResult = ?, TrophyWin = ?, TrophyModelId = ?
            WHERE Id = ?
            """,
            (
                Name,
                Description,
                NationalityName,
                Season,
                TopScorer,
                Picture,
                FinalResult,
                TrophyWin,
                TrophyModelId,
                team_id
            )
        )

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    redirect_url = "/teams"
    params = []

    if filter_name:
        params.append(f"filter_name={filter_name}")
    if sort:
        params.append(f"sort={sort}")

    if params:
        redirect_url += "?" + "&".join(params)

    return RedirectResponse(url=redirect_url, status_code=HTTP_303_SEE_OTHER)


@router.get("/topscorer", response_class=HTMLResponse)
def teams_by_topscorer_page(
    request: Request,
    topscorer: str = Query(None),
    db=Depends(get_db)
):
    cursor = db.cursor()

    query = """
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

    if topscorer and topscorer.strip():
        filters.append("Teams.TopScorer LIKE ?")
        params.append(f"%{topscorer.strip()}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY Teams.Name ASC"

    teams = cursor.execute(query, params).fetchall()
    db.close()

    return templates.TemplateResponse(
        "teams_by_topscorer.html",
        {
            "request": request,
            "teams": teams,
            "topscorer": topscorer
        }
    )