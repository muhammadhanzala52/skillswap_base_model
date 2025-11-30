from sqlalchemy import Column, Integer, String, Text, ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)  
    # Relationships
    skills_offered = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    skills_needed = relationship("SkillRequest", back_populates="user", cascade="all, delete-orphan")

class UserSkill(Base):
    __tablename__ = "user_skills"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_name = Column(String, index=True)
    skill_level = Column(String)  # beginner, intermediate, expert
    
    user = relationship("User", back_populates="skills_offered")

class SkillRequest(Base):
    __tablename__ = "skill_requests" 
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_name = Column(String, index=True)
    description = Column(Text)  # What they want to learn
    
    user = relationship("User", back_populates="skills_needed")