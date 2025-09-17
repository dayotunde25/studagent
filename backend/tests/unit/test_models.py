"""
Unit tests for database models.
"""

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.document import Document
from app.models.flashcard import Flashcard
from app.models.deadline import Deadline
from app.models.match import Match
from app.models.opportunity import Opportunity


class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self, db_session: Session):
        """Test creating a new user."""
        user_data = {
            "email": "test@example.com",
            "hashed_password": "hashed_password",
            "display_name": "Test User",
            "first_name": "Test",
            "last_name": "User",
            "role": "student",
            "is_active": True
        }

        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.role == "student"
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_unique_email(self, db_session: Session):
        """Test that email must be unique."""
        user1_data = {
            "email": "duplicate@example.com",
            "hashed_password": "password1",
            "display_name": "User 1",
            "first_name": "User",
            "last_name": "One",
            "role": "student",
            "is_active": True
        }

        user2_data = {
            "email": "duplicate@example.com",  # Same email
            "hashed_password": "password2",
            "display_name": "User 2",
            "first_name": "User",
            "last_name": "Two",
            "role": "student",
            "is_active": True
        }

        user1 = User(**user1_data)
        db_session.add(user1)
        db_session.commit()

        user2 = User(**user2_data)
        db_session.add(user2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_user_default_values(self, db_session: Session):
        """Test default values for user fields."""
        user_data = {
            "email": "defaults@example.com",
            "hashed_password": "password",
            "display_name": "Default User"
        }

        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.role == "student"  # Default role
        assert user.is_active is True  # Default active status
        assert user.first_name == ""  # Default empty string
        assert user.last_name == ""  # Default empty string

    def test_user_relationships(self, db_session: Session):
        """Test user relationships with other models."""
        user = User(
            email="relations@example.com",
            hashed_password="password",
            display_name="Relation User"
        )
        db_session.add(user)
        db_session.commit()

        # Test documents relationship
        document = Document(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            user_id=user.id
        )
        db_session.add(document)
        db_session.commit()

        # Refresh user to load relationships
        db_session.refresh(user)
        assert len(user.documents) == 1
        assert user.documents[0].filename == "test.pdf"

        # Test flashcards relationship
        flashcard = Flashcard(
            question="What is 2+2?",
            answer="4",
            user_id=user.id,
            document_id=document.id
        )
        db_session.add(flashcard)
        db_session.commit()

        db_session.refresh(user)
        assert len(user.flashcards) == 1
        assert user.flashcards[0].question == "What is 2+2?"


class TestDocumentModel:
    """Test cases for Document model."""

    def test_document_creation(self, db_session: Session):
        """Test creating a new document."""
        user = User(
            email="docuser@example.com",
            hashed_password="password",
            display_name="Doc User"
        )
        db_session.add(user)
        db_session.commit()

        doc_data = {
            "filename": "test_document.pdf",
            "content_type": "application/pdf",
            "size": 2048000,  # 2MB
            "user_id": user.id
        }

        document = Document(**doc_data)
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)

        assert document.id is not None
        assert document.filename == "test_document.pdf"
        assert document.content_type == "application/pdf"
        assert document.size == 2048000
        assert document.user_id == user.id
        assert document.created_at is not None

    def test_document_user_relationship(self, db_session: Session):
        """Test document-user relationship."""
        user = User(
            email="docrel@example.com",
            hashed_password="password",
            display_name="Doc Rel User"
        )
        db_session.add(user)

        document = Document(
            filename="relationship_test.pdf",
            content_type="application/pdf",
            size=1024,
            user_id=user.id
        )
        db_session.add(document)
        db_session.commit()

        # Test reverse relationship
        db_session.refresh(user)
        assert len(user.documents) == 1
        assert user.documents[0].id == document.id


class TestFlashcardModel:
    """Test cases for Flashcard model."""

    def test_flashcard_creation(self, db_session: Session):
        """Test creating a new flashcard."""
        user = User(
            email="flashuser@example.com",
            hashed_password="password",
            display_name="Flash User"
        )
        db_session.add(user)

        document = Document(
            filename="flash_doc.pdf",
            content_type="application/pdf",
            size=1024,
            user_id=user.id
        )
        db_session.add(document)
        db_session.commit()

        flashcard_data = {
            "question": "What is the capital of France?",
            "answer": "Paris",
            "user_id": user.id,
            "document_id": document.id
        }

        flashcard = Flashcard(**flashcard_data)
        db_session.add(flashcard)
        db_session.commit()
        db_session.refresh(flashcard)

        assert flashcard.id is not None
        assert flashcard.question == "What is the capital of France?"
        assert flashcard.answer == "Paris"
        assert flashcard.user_id == user.id
        assert flashcard.document_id == document.id
        assert flashcard.created_at is not None

    def test_flashcard_relationships(self, db_session: Session):
        """Test flashcard relationships."""
        user = User(
            email="flashrel@example.com",
            hashed_password="password",
            display_name="Flash Rel User"
        )
        db_session.add(user)

        document = Document(
            filename="flash_rel.pdf",
            content_type="application/pdf",
            size=1024,
            user_id=user.id
        )
        db_session.add(document)

        flashcard = Flashcard(
            question="Test question",
            answer="Test answer",
            user_id=user.id,
            document_id=document.id
        )
        db_session.add(flashcard)
        db_session.commit()

        # Test user relationship
        db_session.refresh(user)
        assert len(user.flashcards) == 1

        # Test document relationship
        db_session.refresh(document)
        assert len(document.flashcards) == 1


class TestDeadlineModel:
    """Test cases for Deadline model."""

    def test_deadline_creation(self, db_session: Session):
        """Test creating a new deadline."""
        user = User(
            email="deadline@example.com",
            hashed_password="password",
            display_name="Deadline User"
        )
        db_session.add(user)
        db_session.commit()

        deadline_data = {
            "title": "Submit Assignment",
            "description": "Submit the final project",
            "due_date": "2024-12-31T23:59:59Z",
            "priority": "high",
            "user_id": user.id
        }

        deadline = Deadline(**deadline_data)
        db_session.add(deadline)
        db_session.commit()
        db_session.refresh(deadline)

        assert deadline.id is not None
        assert deadline.title == "Submit Assignment"
        assert deadline.description == "Submit the final project"
        assert deadline.priority == "high"
        assert deadline.user_id == user.id
        assert deadline.created_at is not None

    def test_deadline_default_values(self, db_session: Session):
        """Test default values for deadline."""
        user = User(
            email="deaddef@example.com",
            hashed_password="password",
            display_name="Dead Def User"
        )
        db_session.add(user)
        db_session.commit()

        deadline = Deadline(
            title="Test Deadline",
            due_date="2024-12-31T23:59:59Z",
            user_id=user.id
        )
        db_session.add(deadline)
        db_session.commit()
        db_session.refresh(deadline)

        assert deadline.description == ""  # Default empty description
        assert deadline.priority == "medium"  # Default priority
        assert deadline.is_completed is False  # Default completion status


class TestMatchModel:
    """Test cases for Match model."""

    def test_match_creation(self, db_session: Session):
        """Test creating a new match."""
        user1 = User(
            email="user1@example.com",
            hashed_password="password",
            display_name="User One"
        )
        db_session.add(user1)

        user2 = User(
            email="user2@example.com",
            hashed_password="password",
            display_name="User Two"
        )
        db_session.add(user2)
        db_session.commit()

        match_data = {
            "user_id": user1.id,
            "matched_user_id": user2.id,
            "score": 0.85,
            "reason": "Similar interests in Computer Science"
        }

        match = Match(**match_data)
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)

        assert match.id is not None
        assert match.user_id == user1.id
        assert match.matched_user_id == user2.id
        assert match.score == 0.85
        assert match.reason == "Similar interests in Computer Science"
        assert match.created_at is not None


class TestOpportunityModel:
    """Test cases for Opportunity model."""

    def test_opportunity_creation(self, db_session: Session):
        """Test creating a new opportunity."""
        opportunity_data = {
            "title": "Software Engineering Internship",
            "description": "Great opportunity for students",
            "source": "LinkedIn",
            "url": "https://example.com/job",
            "tags": "internship,software,engineering",
            "deadline": "2024-12-31T23:59:59Z"
        }

        opportunity = Opportunity(**opportunity_data)
        db_session.add(opportunity)
        db_session.commit()
        db_session.refresh(opportunity)

        assert opportunity.id is not None
        assert opportunity.title == "Software Engineering Internship"
        assert opportunity.description == "Great opportunity for students"
        assert opportunity.source == "LinkedIn"
        assert opportunity.url == "https://example.com/job"
        assert opportunity.tags == "internship,software,engineering"
        assert opportunity.created_at is not None

    def test_opportunity_defaults(self, db_session: Session):
        """Test default values for opportunity."""
        opportunity = Opportunity(
            title="Test Opportunity",
            description="Test description",
            source="Test Source"
        )
        db_session.add(opportunity)
        db_session.commit()
        db_session.refresh(opportunity)

        assert opportunity.url == ""  # Default empty URL
        assert opportunity.tags == ""  # Default empty tags
        assert opportunity.is_active is True  # Default active status