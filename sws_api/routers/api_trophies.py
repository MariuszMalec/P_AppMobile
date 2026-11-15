from fastapi import APIRouter, Depends, HTTPException

from db import get_db
from services.trophies import list_trophies, update_trophy

router = APIRouter(prefix="/api/trophies", tags=["api-trophies"])


@router.get("")
def get_trophies(db=Depends(get_db)):
    try:
        return list_trophies(db)
    finally:
        db.close()


@router.put("/{trophy_id}")
def put_trophy(trophy_id: int, data: dict, db=Depends(get_db)):
    try:
        result = update_trophy(db, trophy_id, data)
        if result is None:
            raise HTTPException(status_code=404, detail="Trophy not found")
        return result
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
