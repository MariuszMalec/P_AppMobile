from contextlib import asynccontextmanager
import sqlite3
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from db import (
    init_db_if_not_exists,
    insert_orders,
    insert_machines,
)

from routers.home import router as home_router
from routers.harmonogram import router as harmonogram_router
# from routers.teams import router as teams_router


# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "harmonogram.db"
STATIC_DIR = BASE_DIR / "static"


# =========================
# LIFESPAN
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")

        init_db_if_not_exists(conn)
        insert_orders(conn)
        insert_machines(conn)

        conn.commit()
        conn.close()

        yield
    finally:
        conn.close()


# =========================
# APP
# =========================
app = FastAPI(lifespan=lifespan)

# ⬇️ TU PODPINASZ STATIC (WAŻNE: po app = FastAPI)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------- MAIN PAGE ----------
@app.get("/")
def root_redirect():
    return RedirectResponse("/home", status_code=302)


# ---------- ROUTERS ----------
app.include_router(home_router)
app.include_router(harmonogram_router)
# app.include_router(teams_router)
