from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.activity import router as activity_router
from app.api.v1.ai import router as ai_router
from app.api.v1.encounters import router as encounters_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.mcp_skills import router as mcp_router
from app.api.v1.patients import router as patients_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.wallets import router as wallets_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(patients_router)
api_router.include_router(encounters_router)
api_router.include_router(ai_router)
api_router.include_router(mcp_router)
api_router.include_router(inventory_router)
api_router.include_router(portfolio_router)
api_router.include_router(wallets_router)
api_router.include_router(activity_router)
