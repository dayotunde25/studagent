"""
Admin endpoints for system monitoring and management.
"""
from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from app.core.auth import get_current_admin_user
from app.core.database import get_session
from app.models.user import User
from app.models.upload import Upload, Document
from app.models.study import Flashcard, Quiz, Deadline
from app.models.networking import Match, Interaction, Opportunity, Group
from app.models.system import Log, ModelStatus
from app.services.model_router import model_router


router = APIRouter()


@router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get comprehensive system statistics."""
    try:
        stats = {}

        # User statistics
        user_stats = session.exec(
            select(
                func.count(User.id).label("total_users"),
                func.count(User.id).filter(User.is_active == True).label("active_users"),
                func.count(User.id).filter(User.role == "student").label("students"),
                func.count(User.id).filter(User.role == "mentor").label("mentors")
            )
        ).first()

        stats["users"] = {
            "total": user_stats.total_users,
            "active": user_stats.active_users,
            "students": user_stats.students,
            "mentors": user_stats.mentors
        }

        # Content statistics
        content_stats = session.exec(
            select(
                func.count(Upload.id).label("total_uploads"),
                func.count(Document.id).label("total_documents"),
                func.count(Flashcard.id).label("total_flashcards"),
                func.count(Quiz.id).label("total_quizzes")
            )
        ).first()

        stats["content"] = {
            "uploads": content_stats.total_uploads,
            "documents": content_stats.total_documents,
            "flashcards": content_stats.total_flashcards,
            "quizzes": content_stats.total_quizzes
        }

        # Networking statistics
        networking_stats = session.exec(
            select(
                func.count(Match.id).label("total_matches"),
                func.count(Match.id).filter(Match.status == "accepted").label("accepted_matches"),
                func.count(Group.id).label("total_groups"),
                func.count(Interaction.id).label("total_interactions")
            )
        ).first()

        stats["networking"] = {
            "matches": networking_stats.total_matches,
            "accepted_matches": networking_stats.accepted_matches,
            "groups": networking_stats.total_groups,
            "interactions": networking_stats.total_interactions
        }

        # System statistics
        system_stats = session.exec(
            select(
                func.count(Log.id).label("total_logs"),
                func.count(Log.id).filter(Log.level == "ERROR").label("error_logs"),
                func.count(Opportunity.id).label("total_opportunities")
            )
        ).first()

        stats["system"] = {
            "logs": system_stats.total_logs,
            "error_logs": system_stats.error_logs,
            "opportunities": system_stats.total_opportunities
        }

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )


@router.get("/models/status", response_model=Dict[str, Any])
async def get_models_status(
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Get status of all AI models."""
    try:
        status = await model_router.get_model_status()
        return {"models": status}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model status: {str(e)}"
        )


@router.post("/models/{model_name}/retry")
async def retry_model(
    model_name: str,
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Manually retry a failed model."""
    try:
        # Reset circuit breaker for the model
        if model_name in model_router.circuit_breakers:
            circuit_breaker = model_router.circuit_breakers[model_name]
            circuit_breaker.failure_count = 0
            circuit_breaker.state = "CLOSED"
            circuit_breaker.last_failure_time = None

            return {"message": f"Model {model_name} reset successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_name} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry model: {str(e)}"
        )


@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_system_logs(
    skip: int = 0,
    limit: int = 100,
    level: str = None,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get system logs with optional filtering."""
    try:
        query = select(Log).order_by(Log.created_at.desc())

        if level:
            query = query.where(Log.level == level.upper())

        logs = session.exec(query.offset(skip).limit(limit)).all()

        return [
            {
                "id": log.id,
                "level": log.level,
                "message": log.message,
                "module": log.module,
                "function": log.function,
                "user_id": log.user_id,
                "request_id": log.request_id,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )


@router.get("/users", response_model=List[Dict[str, Any]])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get all users with their activity stats."""
    try:
        users = session.exec(
            select(User).offset(skip).limit(limit)
        ).all()

        user_data = []
        for user in users:
            # Get user activity stats
            uploads_count = session.exec(
                select(func.count(Upload.id)).where(Upload.user_id == user.id)
            ).first()

            documents_count = session.exec(
                select(func.count(Document.id))
                .join(Upload, Document.upload_id == Upload.id)
                .where(Upload.user_id == user.id)
            ).first()

            flashcards_count = session.exec(
                select(func.count(Flashcard.id)).where(Flashcard.user_id == user.id)
            ).first()

            user_data.append({
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_active": user.last_active.isoformat() if user.last_active else None,
                "stats": {
                    "uploads": uploads_count,
                    "documents": documents_count,
                    "flashcards": flashcards_count
                }
            })

        return user_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )


@router.post("/maintenance/cleanup")
async def run_cleanup(
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Manually trigger data cleanup."""
    try:
        from app.tasks import cleanup_old_data

        # Run cleanup task synchronously for immediate feedback
        result = cleanup_old_data.apply()

        return {
            "message": "Cleanup completed",
            "result": result.get()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.post("/maintenance/scrape-opportunities")
async def scrape_opportunities(
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Manually trigger opportunity scraping."""
    try:
        from app.tasks import scrape_scholarships

        # Run scraping task synchronously for immediate feedback
        result = scrape_scholarships.apply()

        return {
            "message": "Opportunity scraping completed",
            "result": result.get()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraping failed: {str(e)}"
        )


@router.get("/health")
async def get_health_status(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get comprehensive health status."""
    try:
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }

        # Database health
        try:
            session.exec(select(func.count(User.id)).limit(1))
            health["services"]["database"] = "healthy"
        except Exception as e:
            health["services"]["database"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"

        # Model router health
        try:
            model_status = await model_router.get_model_status()
            healthy_models = sum(1 for m in model_status.values() if m["can_execute"])
            total_models = len(model_status)
            health["services"]["ai_models"] = f"{healthy_models}/{total_models} models healthy"
            if healthy_models == 0:
                health["status"] = "unhealthy"
            elif healthy_models < total_models:
                health["status"] = "degraded"
        except Exception as e:
            health["services"]["ai_models"] = f"unhealthy: {str(e)}"
            health["status"] = "unhealthy"

        return health

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }