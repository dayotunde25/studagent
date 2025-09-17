"""
Upload and document database models.
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel


class Upload(SQLModel, table=True):
    """File upload model."""

    __tablename__ = "uploads"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    filename: str
    filepath: str
    file_type: str  # pdf, doc, docx, txt, etc.
    file_size: int  # in bytes
    parsed_text: Optional[str] = None
    parsing_status: str = Field(default="pending")  # pending, processing, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="uploads")
    documents: list["Document"] = Relationship(back_populates="upload")


class Document(SQLModel, table=True):
    """Processed document model."""

    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    upload_id: int = Field(foreign_key="uploads.id", index=True)
    title: str
    content_summary: str
    full_content: Optional[str] = None
    embeddings: Optional[str] = None  # JSON string of embeddings
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    language: str = Field(default="en")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    upload: Upload = Relationship(back_populates="documents")
    flashcards: list["Flashcard"] = Relationship(back_populates="document")
    quizzes: list["Quiz"] = Relationship(back_populates="document")