from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from templates import templates
from db import get_db


router = APIRouter(prefix="/home", tags=["home"])


@router.get("", response_class=HTMLResponse)
def home_page(request: Request, db=Depends(get_db)):
    stats = {"teams": 0, "seasons": 0, "trophies": 0}

    try:
        cur = db.cursor()
        stats["teams"] = cur.execute("SELECT COUNT(DISTINCT Name) FROM Teams").fetchone()[0]
        stats["seasons"] = cur.execute("SELECT COUNT(DISTINCT Season) FROM Teams").fetchone()[0]
        stats["trophies"] = cur.execute("SELECT COUNT(*) FROM Trophies").fetchone()[0]
    except Exception:
        pass
    finally:
        db.close()

    return templates.TemplateResponse(request, "home.html", {"stats": stats})
