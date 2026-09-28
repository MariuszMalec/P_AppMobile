from fastapi import APIRouter, Depends, HTTPException

from db import get_db
from services.results import get_result_status


router = APIRouter(
    prefix="/api/teams",
    tags=["api-team-trophies"],
)


@router.get("/{team_id}/trophies_by_season")
def get_team_trophies_by_season(
    team_id: int,
    db=Depends(get_db),
):
    cursor = db.cursor()

    team = cursor.execute(
        "SELECT * FROM Teams WHERE Id = ?",
        (team_id,),
    ).fetchone()

    if not team:
        db.close()
        raise HTTPException(404, "Team not found")

    team_name = team["Name"]

    loser_trophy = cursor.execute(
        "SELECT Picture FROM Trophies WHERE Name = ?",
        ("Loser",),
    ).fetchone()

    loser_picture = (
        loser_trophy["Picture"]
        if loser_trophy
        else None
    )

    records = cursor.execute(
        """
        SELECT Season, TrophyModelId, TrophyWin, FinalResult
        FROM Teams
        WHERE Name = ?
        """,
        (team_name,),
    ).fetchall()

    season_map = {}

    for r in records:
        season_map.setdefault(r["Season"], [])

    for r in records:

        if not r["TrophyModelId"]:
            continue

        trophy = cursor.execute(
            "SELECT * FROM Trophies WHERE Id = ?",
            (r["TrophyModelId"],),
        ).fetchone()

        if not trophy:
            continue

        result_status = get_result_status(
            r["FinalResult"],
            team_name,
        )

        season_map[r["Season"]].append(
            {
                "TeamName": team_name,
                "Id": trophy["Id"],
                "Name": trophy["Name"],
                "Picture": trophy["Picture"],
                "Description": trophy["Description"],
                "TrophyWin": r["TrophyWin"],
                "Lose": result_status["lose"],
                "LoserPicture": loser_picture,
            }
        )

    db.close()

    return [
        {
            "TeamName": team_name,
            "Season": season,
            "Trophies": trophies,
        }
        for season, trophies in sorted(season_map.items())
    ]
