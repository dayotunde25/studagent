"""
User and profile database models.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel
from pydantic import EmailStr


class User(SQLModel, table=True):
    """User model with authentication fields."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    display_name: str
    bio: Optional[str] = None
    interests: Optional[str] = None  # JSON string
    skills: Optional[str] = None     # JSON string
    role: str = Field(default="student")  # student, mentor
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: Optional["UserProfile"] = Relationship(back_populates="user")
    uploads: list["Upload"] = Relationship(back_populates="user")
    flashcards: list["Flashcard"] = Relationship(back_populates="user")
    quizzes: list["Quiz"] = Relationship(back_populates="user")
    deadlines: list["Deadline"] = Relationship(back_populates="user")
    interactions: list["Interaction"] = Relationship(back_populates="user")
    matches_as_user: list["Match"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "Match.user_id"}
    )
    matches_as_matched: list["Match"] = Relationship(
        back_populates="matched_user",
        sa_relationship_kwargs={"foreign_keys": "Match.matched_user_id"}
    )


class UserProfile(SQLModel, table=True):
    """Extended user profile information."""

    __tablename__ = "user_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    goals: Optional[str] = None
    year_of_study: Optional[int] = None
    institution: Optional[str] = None
    major: Optional[str] = None
    gpa: Optional[float] = None
    graduation_year: Optional[int] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    # Relationship
    user: User = Relationship(back_populates="profile")