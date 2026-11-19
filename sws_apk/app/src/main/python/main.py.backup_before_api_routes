from contextlib import asynccontextmanager
import sqlite3

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from db import (
    init_db_if_not_exists,
    insert_trophies,
    insert_teams,
)

from routers.home import router as home_router
from routers.trophies import router as trophies_router
from routers.teams import router as teams_router

from routers.api_teams import router as api_teams_router
from routers.api_teams_create import router as api_teams_create_router
from routers.api_teams_edit import router as api_teams_edit_router
from routers.api_teams_delete import router as api_teams_delete_router
from routers.api_team_trophies import router as api_team_trophies_router


# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "sws.db"
STATIC_DIR = BASE_DIR / "static"
REACT_DIR = STATIC_DIR / "react"


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
        insert_trophies(conn)
        insert_teams(conn)

        conn.commit()
        conn.close()

        yield

    finally:
        conn.close()


# =========================
# APP
# =========================
app = FastAPI(lifespan=lifespan)


# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# STATIC
# =========================
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

app.mount(
    "/assets",
    StaticFiles(directory=REACT_DIR / "assets"),
    name="react-assets"
)


# =========================
# REACT MAIN PAGE
# =========================
@app.get("/favicon.svg")
def react_favicon():
    return FileResponse(REACT_DIR / "favicon.svg")


@app.get("/")
def react_index():
    return FileResponse(REACT_DIR / "index.html")


# =========================
# HTML ROUTERS
# =========================
app.include_router(home_router)
app.include_router(trophies_router)
app.include_router(teams_router)


# =========================
# API ROUTERS
# =========================
app.include_router(api_teams_router)
app.include_router(api_teams_create_router)
app.include_router(api_teams_edit_router)
app.include_router(api_teams_delete_router)
app.include_router(api_team_trophies_router)


# =========================
# TEST
# =========================
@app.get("/api/test")
def api_test():
    return {
        "status": "ok",
        "message": "SWS API działa"
    }
