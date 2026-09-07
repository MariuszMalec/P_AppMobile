from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from templates import templates
from db import get_db


router = APIRouter(
    prefix="/home",
    tags=["home"]
)


@router.get("", response_class=HTMLResponse)
def home_page(
    request: Request,
    db=Depends(get_db)
):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request
        }
    )