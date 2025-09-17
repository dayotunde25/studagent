# Database models
from .user import User, UserProfile
from .upload import Upload, Document
from .study import Flashcard, Quiz, Deadline
from .networking import Interaction, Match, Opportunity
from .system import Log, ModelStatus

# Import all models for Alembic
__all__ = [
    "User",
    "UserProfile",
    "Upload",
    "Document",
    "Flashcard",
    "Quiz",
    "Deadline",
    "Interaction",
    "Match",
    "Opportunity",
    "Log",
    "ModelStatus",
]