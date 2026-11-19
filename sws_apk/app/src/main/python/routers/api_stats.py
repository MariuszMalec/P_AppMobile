from fastapi import APIRouter, Depends
from db import get_db
from services.stats import get_insights

router = APIRouter(prefix="/api/stats", tags=["api-stats"])


@router.get("")
def api_stats(db=Depends(get_db)):
    try:
        return get_insights(db)
    finally:
        db.close()
