"""
AI processing endpoints.
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.auth import get_current_user
from app.core.database import get_session
from app.models.upload import Document
from app.schemas.upload import (
    SummaryRequest,
    SummaryResponse,
    FlashcardRequest,
    FlashcardGenerationResponse,
    QuizGenerationRequest,
    QuizGenerationResponse,
    DocumentResponse
)
from app.services.model_router import model_router


router = APIRouter()


SUMMARIZE_PROMPT = """
Task: Summarize the following text for an undergraduate student in simple English.
Output format: JSON { "title": "...", "summary": "...", "key_points": ["...","..."], "recommended_reading": ["..."] }
Text: {text}
"""

FLASHCARD_PROMPT = """
Task: Produce up to {num_cards} flashcards (Q&A) based on the provided content. Each card: {{"q": "...", "a": "...","source": "{{"upload_id": "{upload_id}"}}"}}
Content: {text}
"""

QUIZ_PROMPT = """
Task: Create a {num_questions}-question multiple-choice quiz (4 options each) with answers and explanations based on this content. Provide difficulty (easy/medium/hard) for each question.
Content: {text}
"""


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_text(
    request: SummaryRequest,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Generate summary from text or document."""

    text_content = ""

    if request.document_id:
        # Get document from database
        document = session.get(Document, request.document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Check ownership through upload
        from app.models.upload import Upload
        upload = session.get(Upload, document.upload_id)
        if not upload or upload.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )

        text_content = document.full_content or document.content_summary

    elif request.text:
        text_content = request.text
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either document_id or text must be provided"
        )

    if not text_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No content available for summarization"
        )

    # Generate summary using AI
    try:
        prompt = SUMMARIZE_PROMPT.format(text=text_content[:4000])  # Limit text length
        response_text, model_used = await model_router.call_model(
            prompt=prompt,
            task_type="summarize",
            max_tokens=request.max_length
        )

        # Parse JSON response (simplified for now)
        # In production, you'd want proper JSON parsing with error handling
        summary_data = {
            "title": f"Summary of {document.title if request.document_id else 'Text'}",
            "summary": response_text,
            "key_points": ["Key point 1", "Key point 2"],  # Would parse from AI response
            "recommended_reading": ["Reading 1", "Reading 2"]  # Would parse from AI response
        }

        return SummaryResponse(**summary_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post("/flashcards", response_model=FlashcardGenerationResponse)
async def generate_flashcards(
    request: FlashcardRequest,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Generate flashcards from text or document."""

    text_content = ""
    upload_id = None

    if request.document_id:
        # Get document from database
        document = session.get(Document, request.document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Check ownership through upload
        from app.models.upload import Upload
        upload = session.get(Upload, document.upload_id)
        if not upload or upload.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )

        text_content = document.full_content or document.content_summary
        upload_id = upload.id

    elif request.text:
        text_content = request.text
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either document_id or text must be provided"
        )

    if not text_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No content available for flashcard generation"
        )

    # Generate flashcards using AI
    try:
        prompt = FLASHCARD_PROMPT.format(
            num_cards=request.num_cards,
            text=text_content[:4000],  # Limit text length
            upload_id=upload_id or "text"
        )

        response_text, model_used = await model_router.call_model(
            prompt=prompt,
            task_type="flashcard"
        )

        # Parse response and create flashcards in database
        flashcards = []

        # For now, create sample flashcards
        # In production, you'd parse the AI response properly
        for i in range(min(request.num_cards, 5)):  # Create up to 5 sample cards
            from app.models.study import Flashcard
            flashcard = Flashcard(
                user_id=current_user.id,
                document_id=request.document_id,
                question=f"Sample question {i+1}?",
                answer=f"Sample answer {i+1}",
                source=f'{{"upload_id": "{upload_id or "text"}"}}',
                difficulty="medium"
            )
            session.add(flashcard)
            flashcards.append({"q": flashcard.question, "a": flashcard.answer})

        session.commit()

        return FlashcardGenerationResponse(flashcards=flashcards)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(e)}"
        )


@router.post("/quiz", response_model=QuizGenerationResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Generate quiz from text or document."""

    text_content = ""

    if request.document_id:
        # Get document from database
        document = session.get(Document, request.document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Check ownership through upload
        from app.models.upload import Upload
        upload = session.get(Upload, document.upload_id)
        if not upload or upload.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )

        text_content = document.full_content or document.content_summary

    elif request.text:
        text_content = request.text
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either document_id or text must be provided"
        )

    if not text_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No content available for quiz generation"
        )

    # Generate quiz using AI
    try:
        prompt = QUIZ_PROMPT.format(
            num_questions=request.num_questions,
            text=text_content[:4000]  # Limit text length
        )

        response_text, model_used = await model_router.call_model(
            prompt=prompt,
            task_type="quiz"
        )

        # Create quiz in database
        from app.models.study import Quiz
        quiz = Quiz(
            user_id=current_user.id,
            document_id=request.document_id,
            title=f"Quiz on {document.title if request.document_id else 'Text'}",
            quiz_items='[]',  # Would store parsed quiz items
            max_score=request.num_questions * 10,  # 10 points per question
            difficulty=request.difficulty
        )
        session.add(quiz)
        session.commit()

        # Sample quiz items (would parse from AI response)
        questions = []
        for i in range(min(request.num_questions, 3)):
            questions.append({
                "question": f"Sample question {i+1}?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": 0,
                "explanation": f"Explanation for question {i+1}"
            })

        return QuizGenerationResponse(
            title=quiz.title,
            questions=questions
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )


@router.get("/models/status")
async def get_model_status(
    current_user: Any = Depends(get_current_user)
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