"""
Study groups and collaboration endpoints.
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.database import get_session
from app.models.networking import Group, GroupMember, GroupMessage
from app.schemas.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupWithMembers,
    GroupMemberCreate,
    GroupMemberResponse,
    GroupMessageCreate,
    GroupMessageResponse,
    JoinGroupRequest
)


router = APIRouter()


@router.post("/", response_model=GroupResponse)
async def create_group(
    group_data: GroupCreate,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Create a new study group."""
    group = Group(
        creator_id=current_user.id,
        **group_data.dict()
    )

    session.add(group)
    session.commit()
    session.refresh(group)

    # Add creator as admin member
    creator_member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role="admin"
    )
    session.add(creator_member)
    session.commit()

    # Update member count
    group.member_count = 1
    session.add(group)
    session.commit()

    return GroupResponse.from_orm(group)


@router.get("/", response_model=List[GroupWithMembers])
async def get_groups(
    skip: int = 0,
    limit: int = 100,
    subject: str = None,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get available study groups."""
    query = select(Group)

    if subject:
        query = query.where(Group.subject == subject)

    groups = session.exec(
        query.order_by(Group.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    # Enhance with member info
    result = []
    for group in groups:
        # Get members
        members = session.exec(
            select(GroupMember).where(GroupMember.group_id == group.id)
        ).all()

        # Check if current user is a member
        is_member = any(m.user_id == current_user.id for m in members)
        can_join = not is_member and group.member_count < group.max_members

        group_with_members = GroupWithMembers.from_orm(group)
        group_with_members.members = [
            {"user_id": m.user_id, "role": m.role, "joined_at": m.joined_at.isoformat()}
            for m in members
        ]
        group_with_members.is_member = is_member
        group_with_members.can_join = can_join

        result.append(group_with_members)

    return result


@router.get("/{group_id}", response_model=GroupWithMembers)
async def get_group(
    group_id: int,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get specific group details."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Get members
    members = session.exec(
        select(GroupMember).where(GroupMember.group_id == group.id)
    ).all()

    # Check membership and permissions
    user_member = next((m for m in members if m.user_id == current_user.id), None)
    is_member = user_member is not None
    can_join = not is_member and group.member_count < group.max_members

    # If group is private and user is not a member, deny access
    if group.is_private and not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is a private group"
        )

    group_with_members = GroupWithMembers.from_orm(group)
    group_with_members.members = [
        {"user_id": m.user_id, "role": m.role, "joined_at": m.joined_at.isoformat()}
        for m in members
    ]
    group_with_members.is_member = is_member
    group_with_members.can_join = can_join

    return group_with_members


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_update: GroupUpdate,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Update group details (admin only)."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Check if user is admin
    admin_member = session.exec(
        select(GroupMember)
        .where(GroupMember.group_id == group.id)
        .where(GroupMember.user_id == current_user.id)
        .where(GroupMember.role == "admin")
    ).first()

    if not admin_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can update group details"
        )

    update_data = group_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)

    session.add(group)
    session.commit()
    session.refresh(group)

    return GroupResponse.from_orm(group)


@router.post("/{group_id}/join", response_model=GroupMemberResponse)
async def join_group(
    group_id: int,
    request: JoinGroupRequest,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Join a study group."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Check if already a member
    existing_member = session.exec(
        select(GroupMember)
        .where(GroupMember.group_id == group.id)
        .where(GroupMember.user_id == current_user.id)
    ).first()

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this group"
        )

    # Check capacity
    if group.member_count >= group.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group is full"
        )

    # Add member
    member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role="member"
    )
    session.add(member)

    # Update member count
    group.member_count += 1
    session.add(group)

    session.commit()
    session.refresh(member)

    return GroupMemberResponse.from_orm(member)


@router.post("/{group_id}/leave")
async def leave_group(
    group_id: int,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Leave a study group."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Find member record
    member = session.exec(
        select(GroupMember)
        .where(GroupMember.group_id == group.id)
        .where(GroupMember.user_id == current_user.id)
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a member of this group"
        )

    # Prevent last admin from leaving
    if member.role == "admin":
        admin_count = session.exec(
            select(GroupMember)
            .where(GroupMember.group_id == group.id)
            .where(GroupMember.role == "admin")
        ).all()

        if len(admin_count) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot leave group as the last admin"
            )

    # Remove member
    session.delete(member)

    # Update member count
    group.member_count -= 1
    session.add(group)

    session.commit()

    return {"message": "Successfully left the group"}


@router.get("/{group_id}/messages", response_model=List[GroupMessageResponse])
async def get_group_messages(
    group_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get group messages (members only)."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Check membership
    member = session.exec(
        select(GroupMember)
        .where(GroupMember.group_id == group.id)
        .where(GroupMember.user_id == current_user.id)
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this group"
        )

    messages = session.exec(
        select(GroupMessage)
        .where(GroupMessage.group_id == group.id)
        .order_by(GroupMessage.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    return [GroupMessageResponse.from_orm(msg) for msg in messages]


@router.post("/{group_id}/messages", response_model=GroupMessageResponse)
async def send_group_message(
    group_id: int,
    message_data: GroupMessageCreate,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Send a message to the group (members only)."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Check membership
    member = session.exec(
        select(GroupMember)
        .where(GroupMember.group_id == group.id)
        .where(GroupMember.user_id == current_user.id)
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this group"
        )

    message = GroupMessage(
        group_id=group.id,
        sender_id=current_user.id,
        **message_data.dict()
    )

    session.add(message)
    session.commit()
    session.refresh(message)

    return GroupMessageResponse.from_orm(message)