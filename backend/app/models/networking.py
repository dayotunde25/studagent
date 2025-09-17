"""
Networking and matching database models.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel


class Interaction(SQLModel, table=True):
    """User interaction tracking for matching algorithm."""

    __tablename__ = "interactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    action_type: str  # view_profile, send_message, like, share, etc.
    target_type: str  # user, document, flashcard, etc.
    target_id: int
    interaction_data: str  # JSON string with additional data
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="interactions")


class Match(SQLModel, table=True):
    """Partner/mentor matching results."""

    __tablename__ = "matches"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    matched_user_id: int = Field(foreign_key="users.id", index=True)
    score: float  # matching score 0-1
    reason: str  # explanation of why they match
    match_type: str = Field(default="partner")  # partner, mentor, mentee
    status: str = Field(default="pending")  # pending, accepted, rejected, blocked
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(
        back_populates="matches_as_user",
        sa_relationship_kwargs={"foreign_keys": "Match.user_id"}
    )
    matched_user: "User" = Relationship(
        back_populates="matches_as_matched",
        sa_relationship_kwargs={"foreign_keys": "Match.matched_user_id"}
    )


class Opportunity(SQLModel, table=True):
    """Scholarship and internship opportunities."""

    __tablename__ = "opportunities"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    source: str  # source website/platform
    description: str
    requirements: Optional[str] = None
    tags: str  # JSON string of tags for matching
    location: Optional[str] = None
    deadline: Optional[datetime] = None
    application_url: Optional[str] = None
    opportunity_type: str = Field(default="scholarship")  # scholarship, internship, job
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # These will be computed dynamically
    # match_score: Optional[float] = None  # computed per user
    # matched_users: list[int] = None  # computed per opportunity