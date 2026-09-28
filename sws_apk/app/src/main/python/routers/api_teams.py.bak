from fastapi import APIRouter, Depends, Query
from db import get_db

router = APIRouter(prefix="/api/teams", tags=["api-teams"])


@router.get("")
def get_teams(
    filter_name: str = Query(None),
    filter_trophy: str = Query(None),
    filter_result: str = Query(None),
    sort: str = Query(None),
    db=Depends(get_db),
):
    try:
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

        if filter_name and filter_name.strip():
            filters.append("Teams.Name LIKE ?")
            params.append(f"%{filter_name.strip()}%")

        if filter_trophy and filter_trophy.strip():
            filters.append("Teams.TrophyWin LIKE ?")
            params.append(f"%{filter_trophy.strip()}%")

        if filter_result and filter_result.strip():
            filters.append("Teams.FinalResult LIKE ?")
            params.append(f"%{filter_result.strip()}%")

        if filters:
            query += " WHERE " + " AND ".join(filters)

        if sort == "name_desc":
            query += " ORDER BY Teams.Name DESC, Teams.Season DESC"
        elif sort == "season_asc":
            query += " ORDER BY Teams.Season ASC, Teams.Name ASC"
        elif sort == "season_desc":
            query += " ORDER BY Teams.Season DESC, Teams.Name ASC"
        else:
            query += " ORDER BY Teams.Name ASC, Teams.Season ASC"

        teams = db.execute(query, params).fetchall()

        return [dict(team) for team in teams]

    finally:
        db.close()
