"""
System logging and model status database models.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Log(SQLModel, table=True):
    """Application logging model."""

    __tablename__ = "logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    context: str  # JSON string with additional context
    user_id: Optional[int] = Field(foreign_key="users.id", index=True)
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelStatus(SQLModel, table=True):
    """LLM model health status tracking."""

    __tablename__ = "model_status"

    id: Optional[int] = Field(default=None, primary_key=True)
    model_name: str = Field(unique=True, index=True)
    provider: str  # openrouter, gemini, groq
    status: str = Field(default="healthy")  # healthy, degraded, unhealthy
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    fail_count: int = Field(default=0)
    success_count: int = Field(default=0)
    total_requests: int = Field(default=0)
    average_response_time: Optional[float] = None  # in seconds
    last_success_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)