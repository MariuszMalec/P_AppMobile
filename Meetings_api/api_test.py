from fastapi import APIRouter

router = APIRouter(prefix="/api")

@router.get("/test")
async def api_test():
    return {"message": "Meetings API działa!"}
