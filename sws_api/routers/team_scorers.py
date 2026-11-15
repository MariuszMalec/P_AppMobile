from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from templates import templates
from db import get_db
from services.scorers import get_team_scorers

router = APIRouter(prefix="/teams", tags=["team-scorers"])


@router.get("/scorers", response_class=HTMLResponse)
def team_scorers(request: Request, name: str = Query(None),
                 team_id: int = Query(None), db=Depends(get_db)):
    try:
        return templates.TemplateResponse(
            request, "team_scorers.html", get_team_scorers(db, name, team_id))
    finally:
        db.close()
