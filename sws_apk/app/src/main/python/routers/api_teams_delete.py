from fastapi import APIRouter, Depends, HTTPException
from db import get_db

router = APIRouter(prefix="/api/teams", tags=["api-teams"])


@router.delete("/{team_id}")
def delete_team(team_id: int, db=Depends(get_db)):
    try:
        cursor = db.cursor()

        team = cursor.execute(
            """
            SELECT Id
            FROM Teams
            WHERE Id = ?
            """,
            (team_id,)
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
            (team_id,)
        )

        db.commit()

        return {
            "status": "ok",
            "message": "Team deleted",
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
