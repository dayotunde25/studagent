"""
Pydantic schemas for networking and matching features.
"""
from typing import Optional
from pydantic import BaseModel


class InteractionBase(BaseModel):
    """Base interaction schema."""
    action_type: str
    target_type: str
    target_id: int
    metadata: str = "{}"  # JSON string


class InteractionCreate(InteractionBase):
    """Schema for creating interactions."""
    pass


class InteractionResponse(InteractionBase):
    """Schema for interaction responses."""
    id: int
    user_id: int
    created_at: str

    class Config:
        from_attributes = True


class MatchBase(BaseModel):
    """Base match schema."""
    matched_user_id: int
    score: float
    reason: str
    match_type: str = "partner"


class MatchCreate(MatchBase):
    """Schema for creating matches."""
    pass


class MatchResponse(MatchBase):
    """Schema for match responses."""
    id: int
    user_id: int
    status: str
    created_at: str

    class Config:
        from_attributes = True


class MatchWithUser(MatchResponse):
    """Match response with user details."""
    matched_user: dict  # Simplified user info

    class Config:
        from_attributes = True


class OpportunityBase(BaseModel):
    """Base opportunity schema."""
    title: str
    source: str
    description: str
    requirements: Optional[str] = None
    tags: str  # JSON string of tags
    location: Optional[str] = None
    deadline: Optional[str] = None
    application_url: Optional[str] = None
    opportunity_type: str = "scholarship"


class OpportunityCreate(OpportunityBase):
    """Schema for creating opportunities."""
    pass


class OpportunityResponse(OpportunityBase):
    """Schema for opportunity responses."""
    id: int
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class MatchRequest(BaseModel):
    """Schema for match generation request."""
    limit: int = 10
    match_type: str = "partner"  # partner, mentor, mentee


class MatchAcceptRequest(BaseModel):
    """Schema for accepting a match."""
    message: Optional[str] = None