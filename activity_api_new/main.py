from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from db import (
    init_db_if_not_exists,
    insert_person_families,
    insert_picture_activities,
    insert_activities_days,
)

from routes_activities_home import register_routes_home
from routes_activities_activity import register_routes_activity
from routes_activities_livenow import register_routes_livenow
from routes_activities_pictureactivity import register_routes_pictureactivity


app = FastAPI()


@app.on_event("startup")
def startup():
    init_db_if_not_exists()
    insert_person_families()
    insert_picture_activities()
    insert_activities_days()

# ---------- MAIN PAGE ----------
@app.get("/")
def root_redirect():
    return RedirectResponse("/home", status_code=302)    


# ⬅️ TU REJESTRUJEMY ENDPOINTY
register_routes_home(app)
register_routes_activity(app)
register_routes_livenow(app)
register_routes_pictureactivity(app)

