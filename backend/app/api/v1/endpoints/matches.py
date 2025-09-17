"""
Networking and matching endpoints.
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.database import get_session
from app.models.networking import Match, Interaction, Opportunity
from app.models.user import User
from app.schemas.networking import (
    MatchResponse,
    MatchWithUser,
    MatchRequest,
    MatchAcceptRequest,
    InteractionCreate,
    InteractionResponse,
    OpportunityResponse
)
from app.services.model_router import model_router


router = APIRouter()


@router.post("/generate", response_model=List[MatchWithUser])
async def generate_matches(
    request: MatchRequest,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Generate potential matches for the current user."""
    try:
        # Get all other users (excluding current user)
        other_users = session.exec(
            select(User).where(User.id != current_user.id).where(User.is_active == True)
        ).all()

        if not other_users:
            return []

        # For now, create simple matches based on interests overlap
        # In production, this would use more sophisticated matching algorithms
        matches = []
        for user in other_users[:request.limit]:
            # Calculate simple similarity score based on interests
            score = calculate_similarity_score(current_user, user)

            if score > 0.1:  # Only include matches with some similarity
                match = Match(
                    user_id=current_user.id,
                    matched_user_id=user.id,
                    score=score,
                    reason=f"Shared interests in {get_shared_interests(current_user, user)}",
                    match_type=request.match_type,
                    status="pending"
                )
                session.add(match)

                # Create response with user details
                match_response = MatchWithUser.from_orm(match)
                match_response.matched_user = {
                    "id": user.id,
                    "display_name": user.display_name,
                    "bio": user.bio,
                    "interests": user.interests,
                    "skills": user.skills,
                    "role": user.role
                }
                matches.append(match_response)

        session.commit()
        return matches

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate matches: {str(e)}"
        )


@router.get("/", response_model=List[MatchWithUser])
async def get_user_matches(
    status_filter: str = "all",  # all, pending, accepted, rejected
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get user's matches."""
    query = select(Match).where(Match.user_id == current_user.id)

    if status_filter != "all":
        query = query.where(Match.status == status_filter)

    matches = session.exec(query.order_by(Match.created_at.desc())).all()

    # Enhance with user details
    result = []
    for match in matches:
        matched_user = session.get(User, match.matched_user_id)
        if matched_user:
            match_response = MatchWithUser.from_orm(match)
            match_response.matched_user = {
                "id": matched_user.id,
                "display_name": matched_user.display_name,
                "bio": matched_user.bio,
                "interests": matched_user.interests,
                "skills": matched_user.skills,
                "role": matched_user.role
            }
            result.append(match_response)

    return result


@router.post("/{match_id}/accept", response_model=MatchResponse)
async def accept_match(
    match_id: int,
    request: MatchAcceptRequest,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Accept a match."""
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    # Check ownership
    if match.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to accept this match"
        )

    if match.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match is already {match.status}"
        )

    match.status = "accepted"

    # Log the interaction
    interaction = Interaction(
        user_id=current_user.id,
        action_type="match_accepted",
        target_type="user",
        target_id=match.matched_user_id,
        metadata=f'{{"match_id": {match_id}, "message": "{request.message or ""}"}}'
    )
    session.add(interaction)

    session.add(match)
    session.commit()
    session.refresh(match)

    return MatchResponse.from_orm(match)


@router.post("/{match_id}/reject")
async def reject_match(
    match_id: int,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Reject a match."""
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    # Check ownership
    if match.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reject this match"
        )

    if match.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match is already {match.status}"
        )

    match.status = "rejected"
    session.add(match)
    session.commit()

    return {"message": "Match rejected successfully"}


@router.post("/interactions", response_model=InteractionResponse)
async def log_interaction(
    interaction_data: InteractionCreate,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Log a user interaction."""
    interaction = Interaction(
        user_id=current_user.id,
        **interaction_data.dict()
    )

    session.add(interaction)
    session.commit()
    session.refresh(interaction)

    return InteractionResponse.from_orm(interaction)


@router.get("/opportunities", response_model=List[OpportunityResponse])
async def get_opportunities(
    skip: int = 0,
    limit: int = 100,
    opportunity_type: str = None,
    session: Session = Depends(get_session)
) -> Any:
    """Get available opportunities."""
    query = select(Opportunity).where(Opportunity.is_active == True)

    if opportunity_type:
        query = query.where(Opportunity.opportunity_type == opportunity_type)

    opportunities = session.exec(
        query.order_by(Opportunity.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    return [OpportunityResponse.from_orm(opp) for opp in opportunities]


def calculate_similarity_score(user1: User, user2: User) -> float:
    """Calculate similarity score between two users."""
    try:
        import json

        interests1 = set(json.loads(user1.interests or "[]"))
        interests2 = set(json.loads(user2.interests or "[]"))
        skills1 = set(json.loads(user1.skills or "[]"))
        skills2 = set(json.loads(user2.skills or "[]"))

        # Calculate Jaccard similarity for interests and skills
        interest_similarity = len(interests1 & interests2) / len(interests1 | interests2) if interests1 | interests2 else 0
        skill_similarity = len(skills1 & skills2) / len(skills1 | skills2) if skills1 | skills2 else 0

        # Role compatibility bonus
        role_bonus = 0.2 if (
            (user1.role == "student" and user2.role == "mentor") or
            (user1.role == "mentor" and user2.role == "student")
        ) else 0

        return min(1.0, (interest_similarity * 0.4 + skill_similarity * 0.4 + role_bonus))

    except:
        return 0.1  # Default low similarity


def get_shared_interests(user1: User, user2: User) -> str:
    """Get shared interests as a string."""
    try:
        import json

        interests1 = set(json.loads(user1.interests or "[]"))
        interests2 = set(json.loads(user2.interests or "[]"))

        shared = interests1 & interests2
        return ", ".join(list(shared)[:3]) if shared else "general studies"

    except:
        return "general studies"