"""
Flashcard and quiz database models.
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel


class Flashcard(SQLModel, table=True):
    """Flashcard model for study materials."""

    __tablename__ = "flashcards"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    document_id: Optional[int] = Field(foreign_key="documents.id", index=True)
    question: str
    answer: str
    source: str  # JSON string with source info
    difficulty: str = Field(default="medium")  # easy, medium, hard
    tags: Optional[str] = None  # JSON string of tags
    is_reviewed: bool = Field(default=False)
    review_count: int = Field(default=0)
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="flashcards")
    document: Optional["Document"] = Relationship(back_populates="flashcards")


class Quiz(SQLModel, table=True):
    """Quiz model for assessments."""

    __tablename__ = "quizzes"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    document_id: Optional[int] = Field(foreign_key="documents.id", index=True)
    title: str
    description: Optional[str] = None
    quiz_items: str  # JSON string of quiz questions and answers
    score: Optional[float] = None
    max_score: int = Field(default=100)
    time_taken: Optional[int] = None  # in seconds
    is_completed: bool = Field(default=False)
    difficulty: str = Field(default="medium")  # easy, medium, hard
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="quizzes")
    document: Optional["Document"] = Relationship(back_populates="quizzes")


class Deadline(SQLModel, table=True):
    """Deadline and reminder model."""

    __tablename__ = "deadlines"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str
    description: Optional[str] = None
    due_date: datetime
    priority: str = Field(default="medium")  # low, medium, high
    category: str = Field(default="study")  # study, assignment, exam, project
    reminder_settings: str  # JSON string of reminder settings
    is_completed: bool = Field(default=False)
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="deadlines")