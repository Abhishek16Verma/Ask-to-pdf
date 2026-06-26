from fastapi import APIRouter

from app.api.router.ask import router as ask_router
from app.api.router.health_check import router as health_router
from app.api.router.upload import router as upload_router

router = APIRouter()
router.include_router(ask_router)
router.include_router(upload_router)
router.include_router(health_router)