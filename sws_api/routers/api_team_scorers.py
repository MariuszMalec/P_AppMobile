from fastapi import APIRouter, Depends, Query
from db import get_db
from services.scorers import get_team_scorers

router = APIRouter(prefix="/api/scorers", tags=["api-scorers"])


@router.get("")
def api_scorers(name: str = Query(None), team_id: int = Query(None), db=Depends(get_db)):
    try:
        d = get_team_scorers(db, name, team_id)
        return {
            "names": d["names"],
            "name": d["name"],
            "rows": [dict(r, Top=d["best"].get(r["Season"]) == r["Player"]) for r in d["rows"]],
            "career": [dict(c) for c in d["career"]],
        }
    finally:
        db.close()
