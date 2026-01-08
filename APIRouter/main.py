from fastapi import FastAPI
from routers.live import router as live_router

app = FastAPI()

app.include_router(live_router)
