from fastapi import APIRouter, Request, Form, Query, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.status import HTTP_303_SEE_OTHER
import sqlite3
from templates import templates

from db import get_db
from datetime import datetime


router = APIRouter(
    prefix="/home",
    tags=["home"]
)


# ==============================
# HOME
# ==============================
@router.get("", response_class=HTMLResponse)
def home_page(
    request: Request,
    db = Depends(get_db)
):
    
    try:
        return templates.TemplateResponse(
            request,
            "home.html",
            status_code=200
        )

    except Exception:
        # brak bazy / tabel / inny błąd → pokaż stronę z komunikatem
        return templates.TemplateResponse(
            request,
            "home.html",
            status_code=400
        )

    finally:
        db.close()

