from fastapi import APIRouter, Depends, HTTPException
from db import get_db

router = APIRouter(prefix="/api/teams", tags=["api-teams"])


@router.put("/{team_id}")
def edit_team(
    team_id: int,
    data: dict,
    db=Depends(get_db),
):
    name = (data.get("Name") or "").strip()

    if not name:
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

        description = data.get("Description")
        nationality_name = data.get("NationalityName")
        season = data.get("Season")
        top_scorer = data.get("TopScorer")
        picture = data.get("Picture")
        final_result = data.get("FinalResult")
        trophy_win = data.get("TrophyWin")
        trophy_model_id = data.get("TrophyModelId")

        # Jeżeli FinalResult jest pusty,
        # zachowujemy wartość istniejącą w bazie.
        if not final_result or not str(final_result).strip():
            final_result = existing["FinalResult"]

        # Trophy ustalamy na podstawie wybranego ID.
        if trophy_model_id:
            trophy = cursor.execute(
                """
                SELECT Id, Name
                FROM Trophies
                WHERE Id = ?
                """,
                (trophy_model_id,)
            ).fetchone()

            if not trophy:
                raise HTTPException(
                    status_code=400,
                    detail="Selected trophy does not exist"
                )

            trophy_win = trophy["Name"]
            trophy_model_id = trophy["Id"]

        else:
            trophy_win = "No"
            trophy_model_id = None

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
                name,
                season,
                trophy_win,
                team_id,
            )
        ).fetchone()

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Team with this Name + Season + Trophy already exists!"
            )

        cursor.execute(
            """
            UPDATE Teams
            SET
                Name = ?,
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
                name,
                description,
                nationality_name,
                season,
                top_scorer,
                picture,
                final_result,
                trophy_win,
                trophy_model_id,
                team_id,
            )
        )

        db.commit()

        return {
            "status": "ok",
            "message": "Team updated",
            "Id": team_id,
        }

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
