from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from db import (
    init_db_if_not_exists,
    # insert_person_families,
    # insert_picture_activities,
    # insert_activities_days,
)

from routers.home import router as home_router
from routers.activity import router as activity_router
from routers.mainmenu import router as mainmenu_router
from routers.livenow import router as livenow_router
from routers.pictureactivity import router as pictureactivity_router


# =========================
# LIFESPAN (startup/shutdown)
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    init_db_if_not_exists()
    insert_person_families()
    insert_picture_activities()
    insert_activities_days()

    yield

    # --- SHUTDOWN ---
    # (na razie nic)


# ⬅️ TU PODPINAMY LIFESPAN
app = FastAPI(lifespan=lifespan)


# ---------- MAIN PAGE ----------
@app.get("/")
def root_redirect():
    return RedirectResponse("/home", status_code=302)


# ---------- ROUTERS ----------
app.include_router(home_router)
app.include_router(mainmenu_router)
app.include_router(activity_router)
app.include_router(livenow_router)
app.include_router(pictureactivity_router)
