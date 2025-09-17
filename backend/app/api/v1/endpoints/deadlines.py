"""
Deadline and planner endpoints.
"""
from datetime import datetime, timedelta
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.database import get_session
from app.models.study import Deadline
from app.schemas.deadline import (
    DeadlineCreate,
    DeadlineUpdate,
    DeadlineResponse,
    DeadlineWithReminders,
    ReminderSettings
)


router = APIRouter()


@router.post("/", response_model=DeadlineResponse)
async def create_deadline(
    deadline_data: DeadlineCreate,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Create a new deadline."""
    # Validate due date is in the future
    if deadline_data.due_date <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Due date must be in the future"
        )

    deadline = Deadline(
        user_id=current_user.id,
        **deadline_data.dict()
    )

    session.add(deadline)
    session.commit()
    session.refresh(deadline)

    return DeadlineResponse.from_orm(deadline)


@router.get("/", response_model=List[DeadlineWithReminders])
async def get_user_deadlines(
    skip: int = 0,
    limit: int = 100,
    completed: Optional[bool] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get user's deadlines with optional filtering."""
    query = select(Deadline).where(Deadline.user_id == current_user.id)

    if completed is not None:
        query = query.where(Deadline.is_completed == completed)

    if priority:
        query = query.where(Deadline.priority == priority)

    if category:
        query = query.where(Deadline.category == category)

    # Order by due date (upcoming first)
    query = query.order_by(Deadline.due_date.asc())

    deadlines = session.exec(query.offset(skip).limit(limit)).all()

    # Parse reminder settings and return enhanced response
    result = []
    for deadline in deadlines:
        try:
            import json
            reminder_settings = json.loads(deadline.reminder_settings)
            reminder_parsed = ReminderSettings(**reminder_settings)
        except:
            reminder_parsed = ReminderSettings()

        deadline_with_reminders = DeadlineWithReminders.from_orm(deadline)
        deadline_with_reminders.reminder_settings_parsed = reminder_parsed
        result.append(deadline_with_reminders)

    return result


@router.get("/upcoming", response_model=List[DeadlineWithReminders])
async def get_upcoming_deadlines(
    days: int = 7,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get upcoming deadlines within specified days."""
    cutoff_date = datetime.utcnow() + timedelta(days=days)

    deadlines = session.exec(
        select(Deadline)
        .where(Deadline.user_id == current_user.id)
        .where(Deadline.due_date <= cutoff_date)
        .where(Deadline.is_completed == False)
        .order_by(Deadline.due_date.asc())
    ).all()

    # Parse reminder settings
    result = []
    for deadline in deadlines:
        try:
            import json
            reminder_settings = json.loads(deadline.reminder_settings)
            reminder_parsed = ReminderSettings(**reminder_settings)
        except:
            reminder_parsed = ReminderSettings()

        deadline_with_reminders = DeadlineWithReminders.from_orm(deadline)
        deadline_with_reminders.reminder_settings_parsed = reminder_parsed
        result.append(deadline_with_reminders)

    return result


@router.get("/{deadline_id}", response_model=DeadlineWithReminders)
async def get_deadline(
    deadline_id: int,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get specific deadline by ID."""
    deadline = session.get(Deadline, deadline_id)
    if not deadline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deadline not found"
        )

    # Check ownership
    if deadline.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this deadline"
        )

    # Parse reminder settings
    try:
        import json
        reminder_settings = json.loads(deadline.reminder_settings)
        reminder_parsed = ReminderSettings(**reminder_settings)
    except:
        reminder_parsed = ReminderSettings()

    deadline_with_reminders = DeadlineWithReminders.from_orm(deadline)
    deadline_with_reminders.reminder_settings_parsed = reminder_parsed

    return deadline_with_reminders


@router.put("/{deadline_id}", response_model=DeadlineResponse)
async def update_deadline(
    deadline_id: int,
    deadline_update: DeadlineUpdate,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Update a deadline."""
    deadline = session.get(Deadline, deadline_id)
    if not deadline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deadline not found"
        )

    # Check ownership
    if deadline.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this deadline"
        )

    # Validate due date if being updated
    if deadline_update.due_date and deadline_update.due_date <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Due date must be in the future"
        )

    update_data = deadline_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deadline, field, value)

    # Handle completion
    if deadline_update.is_completed and not deadline.is_completed:
        deadline.completed_at = datetime.utcnow()
    elif deadline_update.is_completed is False and deadline.is_completed:
        deadline.completed_at = None

    session.add(deadline)
    session.commit()
    session.refresh(deadline)

    return DeadlineResponse.from_orm(deadline)


@router.delete("/{deadline_id}")
async def delete_deadline(
    deadline_id: int,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Delete a deadline."""
    deadline = session.get(Deadline, deadline_id)
    if not deadline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deadline not found"
        )

    # Check ownership
    if deadline.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this deadline"
        )

    session.delete(deadline)
    session.commit()

    return {"message": "Deadline deleted successfully"}


@router.post("/{deadline_id}/complete")
async def complete_deadline(
    deadline_id: int,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Mark a deadline as completed."""
    deadline = session.get(Deadline, deadline_id)
    if not deadline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deadline not found"
        )

    # Check ownership
    if deadline.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this deadline"
        )

    if deadline.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deadline is already completed"
        )

    deadline.is_completed = True
    deadline.completed_at = datetime.utcnow()

    session.add(deadline)
    session.commit()

    return {"message": "Deadline marked as completed"}