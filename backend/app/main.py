"""
Main FastAPI application for Studagent.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.api.v1.api import api_router
from app.core.logging import setup_logging
from app.core.auth import get_current_user, get_optional_current_user
from app.models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    setup_logging()
    create_db_and_tables()
    yield
    # Shutdown
    # Add cleanup logic here if needed


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI-Powered Student Super-App",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Set up Jinja2 templates
    templates = Jinja2Templates(directory="app/templates")

    # Mount static files
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # Set up CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add trusted host middleware
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )

    # Include API routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Frontend routes
    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request, current_user: User = Depends(get_optional_current_user)):
        """Home page."""
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "current_user": current_user, "title": "Studagent - AI-Powered Learning"}
        )

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request, current_user: User = Depends(get_optional_current_user)):
        """Login page."""
        if current_user:
            return templates.TemplateResponse(
                "redirect.html",
                {"request": request, "redirect_url": "/dashboard", "message": "Already logged in"}
            )
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "title": "Login - Studagent"}
        )

    @app.get("/register", response_class=HTMLResponse)
    async def register_page(request: Request, current_user: User = Depends(get_optional_current_user)):
        """Register page."""
        if current_user:
            return templates.TemplateResponse(
                "redirect.html",
                {"request": request, "redirect_url": "/dashboard", "message": "Already logged in"}
            )
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "title": "Register - Studagent"}
        )

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
        """User dashboard."""
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "current_user": current_user, "title": "Dashboard - Studagent"}
        )

    @app.get("/upload", response_class=HTMLResponse)
    async def upload_page(request: Request, current_user: User = Depends(get_current_user)):
        """File upload page."""
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "current_user": current_user, "title": "Upload Documents - Studagent"}
        )

    @app.get("/study", response_class=HTMLResponse)
    async def study_page(request: Request, current_user: User = Depends(get_current_user)):
        """Study tools page."""
        return templates.TemplateResponse(
            "study.html",
            {"request": request, "current_user": current_user, "title": "Study Tools - Studagent"}
        )

    @app.get("/network", response_class=HTMLResponse)
    async def network_page(request: Request, current_user: User = Depends(get_current_user)):
        """Networking page."""
        return templates.TemplateResponse(
            "network.html",
            {"request": request, "current_user": current_user, "title": "Networking - Studagent"}
        )

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_page(request: Request, current_user: User = Depends(get_current_user)):
        """Admin dashboard."""
        if current_user.role != "admin":
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Access Denied", "message": "Admin access required"}
            )
        return templates.TemplateResponse(
            "admin/dashboard.html",
            {"request": request, "current_user": current_user, "title": "Admin Dashboard - Studagent"}
        )

    @app.get("/contact", response_class=HTMLResponse)
    async def contact_page(request: Request):
        """Contact page."""
        return templates.TemplateResponse(
            "contact.html",
            {"request": request, "title": "Contact Us - Studagent"}
        )

    @app.get("/feedback", response_class=HTMLResponse)
    async def feedback_page(request: Request):
        """Feedback page."""
        return templates.TemplateResponse(
            "feedback.html",
            {"request": request, "title": "Feedback - Studagent"}
        )

    @app.get("/study", response_class=HTMLResponse)
    async def study_page(request: Request, current_user: User = Depends(get_current_user)):
        """Study tools page."""
        return templates.TemplateResponse(
            "study.html",
            {"request": request, "current_user": current_user, "title": "Study Tools - Studagent"}
        )

    @app.get("/network", response_class=HTMLResponse)
    async def network_page(request: Request, current_user: User = Depends(get_current_user)):
        """Networking page."""
        return templates.TemplateResponse(
            "network.html",
            {"request": request, "current_user": current_user, "title": "Networking - Studagent"}
        )

    @app.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        return {"status": "healthy", "version": "1.0.0"}

    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )