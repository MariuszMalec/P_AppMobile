# routers/live.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime

from db import DB_PATH

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/livenow", response_class=HTMLResponse)
def live_now(request: Request):
    now = datetime.now().strftime("%H:%M")

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT *
            FROM ActiviesDays
            WHERE StartTime <= ? AND EndTime >= ?
        """, (now, now)).fetchall()

    return templates.TemplateResponse(
        "livenow.html",
        {
            "request": request,
            "live_items": rows
        }
    )
