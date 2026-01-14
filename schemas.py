from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
# This defines what data we expect when creating a user
class UserCreate(BaseModel):
    name: str
    email: str  # We'll upgrade to EmailStr later
    password: str  # NEW: Password field

# This defines what data we return when getting a user  
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    # NOTE: We don't include password in response for security!


    class Config:
        from_attributes = True  # This allows converting SQLAlchemy models to Pydantic models

# NEW: Skill schemas
class SkillOfferCreate(BaseModel):
    skill_name: str
    skill_level: str = "intermediate"  # default value

class SkillRequestCreate(BaseModel):
    skill_name: str
    description: Optional[str] = None

class SkillOfferResponse(BaseModel):
    id: int
    skill_name: str
    skill_level: str

    class Config:
        from_attributes = True

class SkillRequestResponse(BaseModel):
    id: int
    skill_name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

# Extended user response with skills
class UserUpdate(BaseModel):
    name: Optional[str] = None
    about: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    twitter_url: Optional[str] = None
class UserWithSkillsResponse(BaseModel):
    id: int
    name: str
    email: str
    about: Optional[str]
    profile_photo: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    twitter_url: Optional[str]
    skills_offered: List[SkillOfferResponse] = []
    skills_needed: List[SkillRequestResponse] = []

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    receiver_email: str
    content: str

class MessageResponse(BaseModel):
    id: int
    sender_name: str
    sender_email: str
    receiver_name: str
    receiver_email: str
    content: str
    timestamp: datetime
    is_read: bool
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    other_user_name: str
    other_user_email: str
    last_message: Optional[str]
    last_message_time: Optional[datetime]
    unread_count: int = 0




class VideoSessionCreate(BaseModel):
    user1_email: str
    user2_email: str

class VideoSessionResponse(BaseModel):
    id: int
    room_id: str
    user1_email: str
    user2_email: str
    meeting_url: str
    status: str
    created_at: datetime

# Feed Schemas
class PostCreate(BaseModel):
    content: str
    category: str

class PostResponse(BaseModel):
    id: int
    author_email: str
    content: str
    category: str
    created_at: datetime

    class Config:
        from_attributes = True

# Group Chat Schemas
class GroupMessageCreate(BaseModel):
    content: str

class GroupMessageResponse(BaseModel):
    id: int
    sender_email: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class GroupChatResponse(BaseModel):
    id: int
    name: str
    description: str
    
    class Config:
        from_attributes = True