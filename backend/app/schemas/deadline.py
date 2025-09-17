"""
Pydantic schemas for deadlines and planner features.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DeadlineBase(BaseModel):
    """Base deadline schema."""
    title: str
    description: Optional[str] = None
    due_date: datetime
    priority: str = Field(default="medium", regex="^(low|medium|high)$")
    category: str = Field(default="study", regex="^(study|assignment|exam|project)$")
    reminder_settings: str = Field(default='{"enabled": true, "advance_notice": [1, 24]}')  # JSON string


class DeadlineCreate(DeadlineBase):
    """Schema for creating deadlines."""
    pass


class DeadlineUpdate(BaseModel):
    """Schema for updating deadlines."""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(default=None, regex="^(low|medium|high)$")
    category: Optional[str] = Field(default=None, regex="^(study|assignment|exam|project)$")
    reminder_settings: Optional[str] = None
    is_completed: Optional[bool] = None


class DeadlineResponse(DeadlineBase):
    """Schema for deadline responses."""
    id: int
    user_id: int
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ReminderSettings(BaseModel):
    """Schema for reminder settings."""
    enabled: bool = True
    advance_notice: list[int] = Field(default=[1, 24])  # Hours before deadline


class DeadlineWithReminders(DeadlineResponse):
    """Deadline response with parsed reminder settings."""
    reminder_settings_parsed: ReminderSettings

    class Config:
        from_attributes = True