from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Integer, default=0)  # 0 = unread, 1 = read
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])