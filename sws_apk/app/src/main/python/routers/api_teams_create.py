from fastapi import APIRouter, Depends, HTTPException
from db import get_db
from services.teams import create_team as create_team_service

router = APIRouter(prefix="/api/teams", tags=["api-teams"])


@router.post("")
def create_team(
    data: dict,
    db=Depends(get_db),
):
    try:
        return create_team_service(
            db,
            name=data.get("Name"),
            description=data.get("Description"),
            nationality_name=data.get("NationalityName"),
            season=data.get("Season"),
            top_scorer=data.get("TopScorer"),
            picture=data.get("Picture"),
            final_result=data.get("FinalResult"),
            trophy_model_id=data.get("TrophyModelId"),
        )

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
