from fastapi import APIRouter, Request, Form, Depends, HTTPException, Body, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from starlette.status import HTTP_303_SEE_OTHER
from typing import List, Dict
from templates import templates
from db import get_db
from services.results import get_result_status
from services.teams import delete_team as delete_team_service
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

    loser_trophy = cursor.execute(
        "SELECT Picture FROM Trophies WHERE Name = ?",
        ("Loser",)
    ).fetchone()

    loser_picture = loser_trophy["Picture"] if loser_trophy else None

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

        result_status = get_result_status(
            r["FinalResult"],
            team_name,
        )

        lose = result_status["lose"]

        season_map[r["Season"]].append({
            "TeamName": team_name,
            "Id": trophy["Id"],
            "Name": trophy["Name"],
            "Picture": trophy["Picture"],
            "Description": trophy["Description"],
            "TrophyWin": r["TrophyWin"],
            "Lose": lose,
            "LoserPicture": loser_picture
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

@router.get("/trophies/options")
def get_trophy_options(db=Depends(get_db)):
    try:
        trophies = db.execute("""
            SELECT Id, Name
            FROM Trophies
            ORDER BY Name ASC
        """).fetchall()

        return [
            {
                "Id": trophy["Id"],
                "Name": trophy["Name"]
            }
            for trophy in trophies
        ]

    finally:
        db.close()


@router.post("/create", response_class=HTMLResponse)
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
    filter_trophy: str = Form(None),
    filter_result: str = Form(None),
    sort: str = Form(None),
    db=Depends(get_db)
):
    from services.teams import create_team as create_team_service

    params = {}

    if filter_name:
        params["filter_name"] = filter_name

    if filter_trophy:
        params["filter_trophy"] = filter_trophy

    if filter_result:
        params["filter_result"] = filter_result

    if sort:
        params["sort"] = sort

    redirect_url = "/teams"
    if params:
        redirect_url += "?" + urlencode(params)

    try:
        create_team_service(
            db,
            name=Name,
            description=Description,
            nationality_name=NationalityName,
            season=Season,
            top_scorer=TopScorer,
            picture=Picture,
            final_result=FinalResult,
            trophy_model_id=TrophyModelId,
        )

    except HTTPException as e:
        db.rollback()

        if e.status_code == 409:
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
            query_params = []

            if filter_name and filter_name.strip():
                filters.append("Teams.Name LIKE ?")
                query_params.append(f"%{filter_name.strip()}%")

            if filter_trophy and filter_trophy.strip():
                filters.append("Teams.TrophyWin LIKE ?")
                query_params.append(f"%{filter_trophy.strip()}%")

            if filter_result and filter_result.strip():
                filters.append("Teams.FinalResult LIKE ?")
                query_params.append(f"%{filter_result.strip()}%")

            if filters:
                base_query += " WHERE " + " AND ".join(filters)

            if sort == "name_desc":
                base_query += " ORDER BY Teams.Name DESC, Teams.Season DESC"
            else:
                base_query += " ORDER BY Teams.Name ASC, Teams.Season ASC"

            teams = cursor.execute(
                base_query,
                query_params
            ).fetchall()

            return templates.TemplateResponse(
                request,
                "teams.html",
                {
                    "teams": teams,
                    "filter_name": filter_name,
                    "filter_trophy": filter_trophy,
                    "filter_result": filter_result,
                    "sort": sort,
                    "error": "Team with this Name + Season + Trophy already exists!",
                    "open_create_team_modal": True
                }
            )

        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()

    return RedirectResponse(
        url=redirect_url,
        status_code=HTTP_303_SEE_OTHER
    )


@router.post("/{team_id}/delete")
def delete_team(
    team_id: int,
    request: Request,
    filter_name: str = Form(None),
    filter_trophy: str = Form(None),
    filter_result: str = Form(None),
    sort: str = Form(None),
    db=Depends(get_db)
):
    try:
        delete_team_service(db, team_id)

    except HTTPException:
        # Nie zamykamy bazy przed rollbackiem.
        # 404 ma pozostać 404.
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()

    params = {}

    if filter_name:
        params["filter_name"] = filter_name

    if filter_trophy:
        params["filter_trophy"] = filter_trophy

    if filter_result:
        params["filter_result"] = filter_result

    if sort:
        params["sort"] = sort

    redirect_url = "/teams"

    if params:
        redirect_url += "?" + urlencode(params)

    return RedirectResponse(
        url=redirect_url,
        status_code=HTTP_303_SEE_OTHER
    )


@router.get("/{team_id}/edit", response_class=HTMLResponse)
def edit_team_form(
    team_id: int,
    request: Request,
    db=Depends(get_db)
):
    cursor = db.cursor()

    team = cursor.execute(
        """
        SELECT *
        FROM Teams
        WHERE Id = ?
        """,
        (team_id,)
    ).fetchone()

    if not team:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    # Pobierz trofea do listy wyboru
    trophies = cursor.execute(
        """
        SELECT Id, Name
        FROM Trophies
        ORDER BY Name ASC
        """
    ).fetchall()

    db.close()

    return templates.TemplateResponse(
        request,
        "edit_team.html",
        {
            "team": team,
            "trophies": trophies,
            "filter_name": request.query_params.get("filter_name"),
            "filter_trophy": request.query_params.get("filter_trophy"),
            "filter_result": request.query_params.get("filter_result"),
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
    filter_trophy: str = Form(None),
    filter_result: str = Form(None),
    sort: str = Form(None),
    db=Depends(get_db)
):
    if not Name.strip():
        raise HTTPException(
            status_code=400,
            detail="Team name cannot be empty"
        )

    try:
        cursor = db.cursor()

        existing = cursor.execute(
            """
            SELECT *
            FROM Teams
            WHERE Id = ?
            """,
            (team_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Team not found"
            )

        # ============================================================
        # SPRAWDZENIE FINAL RESULT
        # ============================================================

        # Jeżeli formularz nie przesłał FinalResult,
        # zachowujemy wartość istniejącą w bazie.
        if not FinalResult or not FinalResult.strip():
            FinalResult = existing["FinalResult"]

        # ============================================================
        # TROPHY - ID USTALAMY NA PODSTAWIE WYBRANEGO TROPHY WIN
        # ============================================================

        if TrophyWin and TrophyWin != "No":

            trophy = cursor.execute(
                """
                SELECT Id, Name
                FROM Trophies
                WHERE Name = ?
                """,
                (TrophyWin,)
            ).fetchone()

            if not trophy:
                raise HTTPException(
                    status_code=400,
                    detail="Selected trophy does not exist"
                )

            TrophyWin = trophy["Name"]
            TrophyModelId = trophy["Id"]

        else:
            TrophyWin = "No"
            TrophyModelId = None

        # ============================================================
        # SPRAWDZENIE DUPLIKATU
        # ============================================================

        duplicate = cursor.execute(
            """
            SELECT Id
            FROM Teams
            WHERE Name = ?
              AND Season = ?
              AND TrophyWin = ?
              AND Id != ?
            """,
            (
                Name,
                Season,
                TrophyWin,
                team_id
            )
        ).fetchone()

        if duplicate:
            return templates.TemplateResponse(
                request,
                "edit_team.html",
                {
                    "team": {
                        "Id": team_id,
                        "Name": Name,
                        "Description": Description,
                        "NationalityName": NationalityName,
                        "Season": Season,
                        "TopScorer": TopScorer,
                        "Picture": Picture,
                        "FinalResult": FinalResult,
                        "TrophyWin": TrophyWin,
                        "TrophyModelId": TrophyModelId,
                    },
                    "trophies": cursor.execute(
                        """
                        SELECT Id, Name
                        FROM Trophies
                        ORDER BY Name ASC
                        """
                    ).fetchall(),
                    "filter_name": filter_name,
                    "filter_trophy": filter_trophy,
                    "filter_result": filter_result,
                    "sort": sort,
                    "error": "Team with this Name + Season + Trophy already exists!"
                }
            )

        # ============================================================
        # UPDATE
        # ============================================================

        cursor.execute(
            """
            UPDATE Teams
            SET Name = ?,
                Description = ?,
                NationalityName = ?,
                Season = ?,
                TopScorer = ?,
                Picture = ?,
                FinalResult = ?,
                TrophyWin = ?,
                TrophyModelId = ?
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

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()

    params = {}

    if filter_name:
        params["filter_name"] = filter_name

    if filter_trophy:
        params["filter_trophy"] = filter_trophy

    if filter_result:
        params["filter_result"] = filter_result

    if sort:
        params["sort"] = sort

    redirect_url = "/teams"

    if params:
        redirect_url += "?" + urlencode(params)

    return RedirectResponse(
        url=redirect_url,
        status_code=HTTP_303_SEE_OTHER
    )


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
        request,
        "teams_by_topscorer.html",
        {
            "teams": teams,
            "topscorer": topscorer
        }
    )