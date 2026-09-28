from fastapi import APIRouter, Depends, HTTPException

from db import get_db
from services.teams import delete_team as delete_team_service


router = APIRouter(
    prefix="/api/teams",
    tags=["api-teams"],
)


@router.delete("/{team_id}")
def delete_team(team_id: int, db=Depends(get_db)):
    try:
        return delete_team_service(db, team_id)

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
