from fastapi import APIRouter, Depends, HTTPException
from db import get_db

router = APIRouter(
    prefix="/api/teams",
    tags=["api-team-trophies"]
)


@router.get("/{team_id}/trophies_by_season")
def get_team_trophies_by_season(
    team_id: int,
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

    season_map = {}

    for r in records:
        season_map.setdefault(r["Season"], [])

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

        lose = False

        if "winner" in result_lower:
            lose = False

        elif "round" in result_lower or ":" not in result:
            lose = True

        else:
            try:
                import re

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
