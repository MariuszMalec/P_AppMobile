from contextlib import asynccontextmanager
import sqlite3
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pathlib import Path

from db import (
    init_db_if_not_exists,
    insert_trophies,

)

from routers.home import router as home_router
from routers.trophies import router as trophies_router
from routers.teams import router as teams_router


# =========================
# LIFESPAN (startup/shutdown)
# =========================
DB_PATH = Path(__file__).parent / "sws.db"


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # konfiguracja bazy RAZ na start
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")

        init_db_if_not_exists(conn)
        insert_trophies(conn)

        conn.commit()
        conn.close()   # ← zamykasz TU

        yield  # start aplikacji
    finally:
        conn.close()  # shutdown


# ⬅️ TU PODPINAMY LIFESPAN
app = FastAPI(lifespan=lifespan)

# ---------- MAIN PAGE ----------
@app.get("/")
def root_redirect():
    return RedirectResponse("/home", status_code=302)


# ---------- ROUTERS ----------
app.include_router(home_router)
app.include_router(trophies_router)
app.include_router(teams_router)

