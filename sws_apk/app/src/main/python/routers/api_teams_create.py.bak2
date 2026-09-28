from fastapi import APIRouter, Depends, HTTPException
from db import get_db

router = APIRouter(prefix="/api/teams", tags=["api-teams"])


@router.post("")
def create_team(
    data: dict,
    db=Depends(get_db),
):
    name = (data.get("Name") or "").strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Team name cannot be empty"
        )

    description = data.get("Description")
    nationality_name = data.get("NationalityName")
    season = data.get("Season")
    top_scorer = data.get("TopScorer")
    picture = data.get("Picture")
    final_result = data.get("FinalResult")
    trophy_model_id = data.get("TrophyModelId")

    # ============================================================
    # POPRAWA FORMATU FINAL RESULT
    # ============================================================

    if final_result:
        final_result = final_result.strip()

        if ":" in final_result:
            parts = final_result.rsplit(":", 2)

            if len(parts) == 3:
                team_part = parts[0].strip()
                goals_a = parts[1].strip()
                goals_b = parts[2].strip()

                if (
                    team_part
                    and goals_a.isdigit()
                    and goals_b.isdigit()
                ):
                    if not team_part.endswith(" "):
                        final_result = (
                            f"{team_part} "
                            f"{goals_a}:{goals_b}"
                        )

    if not final_result:
        final_result = ""

    try:
        cursor = db.cursor()

        # ============================================================
        # SPRAWDZENIE TROFEUM
        # ============================================================

        trophy_win = None

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
                trophy_model_id = None
            else:
                trophy_win = trophy["Name"]

        if not trophy_win:
            trophy_win = "No"
            trophy_model_id = None

        # ============================================================
        # SPRAWDZENIE DUPLIKATU
        # ============================================================

        existing = cursor.execute(
            """
            SELECT Id
            FROM Teams
            WHERE Name = ? AND Season = ? AND TrophyWin = ?
            """,
            (name, season, trophy_win)
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Team with this Name + Season + Trophy already exists!"
            )

        # ============================================================
        # INSERT
        # ============================================================

        cursor.execute(
            """
            INSERT INTO Teams
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            )
        )

        db.commit()

        team_id = cursor.lastrowid

        return {
            "status": "ok",
            "message": "Team created",
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
