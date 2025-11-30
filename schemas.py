from pydantic import BaseModel
from typing import List, Optional

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
class UserWithSkillsResponse(BaseModel):
    id: int
    name: str
    email: str
    skills_offered: List[SkillOfferResponse] = []
    skills_needed: List[SkillRequestResponse] = []

    class Config:
        from_attributes = True
