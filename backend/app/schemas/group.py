"""
Pydantic schemas for study groups and collaboration features.
"""
from typing import Optional, List
from pydantic import BaseModel


class GroupBase(BaseModel):
    """Base study group schema."""
    name: str
    description: Optional[str] = None
    subject: str
    max_members: int = 10
    is_private: bool = False
    meeting_schedule: Optional[str] = None  # JSON string


class GroupCreate(GroupBase):
    """Schema for creating study groups."""
    pass


class GroupUpdate(BaseModel):
    """Schema for updating study groups."""
    name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    max_members: Optional[int] = None
    is_private: Optional[bool] = None
    meeting_schedule: Optional[str] = None


class GroupResponse(GroupBase):
    """Schema for group responses."""
    id: int
    creator_id: int
    member_count: int
    created_at: str

    class Config:
        from_attributes = True


class GroupMemberBase(BaseModel):
    """Base group member schema."""
    user_id: int
    role: str = "member"  # member, moderator, admin


class GroupMemberCreate(GroupMemberBase):
    """Schema for adding group members."""
    pass


class GroupMemberResponse(GroupMemberBase):
    """Schema for group member responses."""
    id: int
    group_id: int
    joined_at: str

    class Config:
        from_attributes = True


class GroupWithMembers(GroupResponse):
    """Group response with member details."""
    members: List[dict]  # Simplified member info
    is_member: bool
    can_join: bool

    class Config:
        from_attributes = True


class GroupMessageBase(BaseModel):
    """Base group message schema."""
    content: str
    message_type: str = "text"  # text, file, system


class GroupMessageCreate(GroupMessageBase):
    """Schema for creating group messages."""
    pass


class GroupMessageResponse(GroupMessageBase):
    """Schema for group message responses."""
    id: int
    group_id: int
    sender_id: int
    created_at: str

    class Config:
        from_attributes = True


class JoinGroupRequest(BaseModel):
    """Schema for joining a group."""
    message: Optional[str] = None


class GroupInvitation(BaseModel):
    """Schema for group invitations."""
    group_id: int
    invited_user_id: int
    message: Optional[str] = None