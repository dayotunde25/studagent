"""
Pydantic schemas for file uploads and documents.
"""
from typing import Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Schema for upload response."""
    id: int
    filename: str
    file_type: str
    file_size: int
    parsing_status: str
    created_at: str

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: int
    upload_id: int
    title: str
    content_summary: str
    word_count: Optional[int]
    page_count: Optional[int]
    language: str
    created_at: str

    class Config:
        from_attributes = True


class FlashcardResponse(BaseModel):
    """Schema for flashcard response."""
    id: int
    question: str
    answer: str
    difficulty: str
    tags: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    """Schema for quiz response."""
    id: int
    title: str
    score: Optional[float]
    max_score: int
    is_completed: bool
    difficulty: str
    created_at: str

    class Config:
        from_attributes = True


class QuizItem(BaseModel):
    """Schema for individual quiz question."""
    question: str
    options: list[str]
    correct_answer: int
    explanation: str


class QuizGenerationRequest(BaseModel):
    """Schema for quiz generation request."""
    document_id: Optional[int] = None
    text: Optional[str] = None
    num_questions: int = 10
    difficulty: str = "medium"


class SummaryRequest(BaseModel):
    """Schema for summary generation request."""
    document_id: Optional[int] = None
    text: Optional[str] = None
    max_length: int = 500


class FlashcardRequest(BaseModel):
    """Schema for flashcard generation request."""
    document_id: Optional[int] = None
    text: Optional[str] = None
    num_cards: int = 10


class SummaryResponse(BaseModel):
    """Schema for summary response."""
    title: str
    summary: str
    key_points: list[str]
    recommended_reading: list[str]


class FlashcardGenerationResponse(BaseModel):
    """Schema for flashcard generation response."""
    flashcards: list[dict]


class QuizGenerationResponse(BaseModel):
    """Schema for quiz generation response."""
    title: str
    questions: list[QuizItem]