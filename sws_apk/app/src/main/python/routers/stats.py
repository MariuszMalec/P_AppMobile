from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from templates import templates
from db import get_db
from services.stats import get_insights

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_class=HTMLResponse)
def stats_page(request: Request, db=Depends(get_db)):
    try:
        insights = get_insights(db)
    finally:
        db.close()
    return templates.TemplateResponse(request, "stats.html", {"insights": insights})
