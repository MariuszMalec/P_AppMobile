from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from templates import templates


router = APIRouter(
    prefix="/home",
    tags=["home"]
)


@router.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html"
    )
