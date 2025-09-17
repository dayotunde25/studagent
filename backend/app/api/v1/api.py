"""
Main API router that includes all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, uploads, ai


api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
# TODO: Add other routers as they are implemented
# api_router.include_router(deadlines.router, prefix="/deadlines", tags=["deadlines"])
# api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
# api_router.include_router(admin.router, prefix="/admin", tags=["admin"])