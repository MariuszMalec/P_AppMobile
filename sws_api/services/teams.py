from fastapi import HTTPException


def delete_team(db, team_id: int):
    cursor = db.cursor()

    team = cursor.execute(
        """
        SELECT Id
        FROM Teams
        WHERE Id = ?
        """,
        (team_id,),
    ).fetchone()

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    cursor.execute(
        """
        DELETE FROM Teams
        WHERE Id = ?
        """,
        (team_id,),
    )

    db.commit()

    return {
        "status": "ok",
        "message": "Team deleted",
        "Id": team_id,
    }


def create_team(
    db,
    name,
    description=None,
    nationality_name=None,
    season=None,
    top_scorer=None,
    picture=None,
    final_result=None,
    trophy_model_id=None,
):
    name = (name or "").strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Team name cannot be empty"
        )

    # POPRAWA FORMATU FINAL RESULT
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

    cursor = db.cursor()

    # SPRAWDZENIE TROFEUM
    trophy_win = None

    if trophy_model_id:
        trophy = cursor.execute(
            """
            SELECT Id, Name
            FROM Trophies
            WHERE Id = ?
            """,
            (trophy_model_id,),
        ).fetchone()

        if not trophy:
            trophy_model_id = None
        else:
            trophy_win = trophy["Name"]

    if not trophy_win:
        trophy_win = "No"
        trophy_model_id = None

    # SPRAWDZENIE DUPLIKATU
    existing = cursor.execute(
        """
        SELECT Id
        FROM Teams
        WHERE Name = ?
          AND Season = ?
          AND TrophyWin = ?
        """,
        (name, season, trophy_win),
    ).fetchone()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Team with this Name + Season + Trophy already exists!"
        )

    # INSERT
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
        ),
    )

    db.commit()

    team_id = cursor.lastrowid

    return {
        "status": "ok",
        "message": "Team created",
        "Id": team_id,
    }
